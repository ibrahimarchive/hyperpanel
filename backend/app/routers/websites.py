"""
Websites API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole
from app.models.website import Website, WebsiteType, WebsiteStatus
from app.models.database_model import Database, DatabaseUser
from app.models.activity_log import ActivityLog
from app.schemas.website import WebsiteCreate, WebsiteUpdate, WebsiteResponse, WordPressInstallRequest
from app.services.nginx_service import nginx_service
from app.services.wordpress_service import wordpress_service
from app.config import settings

router = APIRouter(prefix="/api/websites", tags=["Websites"])


@router.get("")
async def list_websites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all websites (admin sees all, users see their own)."""
    query = select(Website)
    if user.role != UserRole.ADMIN:
        query = query.where(Website.user_id == user.id)
    query = query.order_by(Website.created_at.desc())

    result = await db.execute(query)
    websites = result.scalars().all()

    return [
        {
            "id": w.id,
            "user_id": w.user_id,
            "name": w.name,
            "domain": w.domain,
            "site_type": w.site_type.value if hasattr(w.site_type, 'value') else w.site_type,
            "status": w.status.value if hasattr(w.status, 'value') else w.status,
            "document_root": w.document_root,
            "php_version": w.php_version,
            "proxy_port": w.proxy_port,
            "ssl_enabled": w.ssl_enabled,
            "force_https": w.force_https,
            "description": w.description,
            "created_at": w.created_at.isoformat() if w.created_at else None,
            "updated_at": w.updated_at.isoformat() if w.updated_at else None,
        }
        for w in websites
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_website(
    data: WebsiteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new website with Nginx configuration."""
    # Check limits
    count_result = await db.execute(
        select(Website).where(Website.user_id == user.id)
    )
    current_count = len(count_result.scalars().all())
    if user.role != UserRole.ADMIN and current_count >= user.max_websites:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Website limit reached ({user.max_websites})",
        )

    # Check domain uniqueness
    existing = await db.execute(
        select(Website).where(Website.domain == data.domain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Domain '{data.domain}' already exists",
        )

    # Create Nginx config and document root
    nginx_result = await nginx_service.create_website(
        domain=data.domain,
        site_type=data.site_type,
        php_version=data.php_version or "8.2",
        proxy_port=data.proxy_port,
        proxy_address=data.proxy_address or "127.0.0.1",
    )

    if not nginx_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create website: {nginx_result.get('error', 'Unknown error')}",
        )

    # Save to database
    website = Website(
        user_id=user.id,
        name=data.name,
        domain=data.domain,
        site_type=WebsiteType(data.site_type),
        status=WebsiteStatus.ACTIVE,
        document_root=nginx_result["document_root"],
        access_log=nginx_result.get("access_log"),
        error_log=nginx_result.get("error_log"),
        php_version=data.php_version,
        proxy_port=data.proxy_port,
        proxy_address=data.proxy_address,
        description=data.description,
    )
    db.add(website)

    # Log activity
    log = ActivityLog(
        user_id=user.id,
        action="website.create",
        category="website",
        description=f"Created website '{data.domain}'",
        resource_type="website",
        resource_name=data.domain,
    )
    db.add(log)

    await db.flush()
    await db.refresh(website)

    return {
        "id": website.id,
        "domain": website.domain,
        "document_root": website.document_root,
        "status": "active",
        "message": f"Website '{data.domain}' created successfully",
    }


@router.post("/wordpress", status_code=status.HTTP_201_CREATED)
async def install_wordpress(
    data: WordPressInstallRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """1-Click automated WordPress deployment."""
    # Check limits
    count_result = await db.execute(
        select(Website).where(Website.user_id == user.id)
    )
    current_count = len(count_result.scalars().all())
    if user.role != UserRole.ADMIN and current_count >= user.max_websites:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Website limit reached ({user.max_websites})",
        )

    # Check domain uniqueness
    existing = await db.execute(
        select(Website).where(Website.domain == data.domain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Domain '{data.domain}' already exists",
        )

    # Run installation
    install_res = await wordpress_service.install_wordpress(
        domain=data.domain,
        site_title=data.site_title,
        admin_username=data.admin_username,
        admin_password=data.admin_password,
        admin_email=data.admin_email,
        php_version=data.php_version or "8.2",
    )

    if not install_res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=install_res.get("error", "WordPress installation failed"),
        )

    # Record website
    website = Website(
        user_id=user.id,
        name=data.site_title,
        domain=data.domain,
        site_type=WebsiteType.PHP,
        status=WebsiteStatus.ACTIVE,
        document_root=install_res["document_root"],
        php_version=data.php_version or "8.2",
        description=f"WordPress: {data.site_title}",
    )
    db.add(website)
    await db.flush()
    await db.refresh(website)

    # Record database
    db_record = Database(
        user_id=user.id,
        name=install_res["db_name"],
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
        website_id=website.id,
    )
    db.add(db_record)
    await db.flush()

    # Record database user
    db_user_record = DatabaseUser(
        user_id=user.id,
        username=install_res["db_user"],
        host="localhost",
        database_ids=str(db_record.id),
        privileges="ALL",
    )
    db.add(db_user_record)

    log = ActivityLog(
        user_id=user.id,
        action="website.wordpress_install",
        category="website",
        description=f"Installed WordPress on '{data.domain}'",
        resource_type="website",
        resource_name=data.domain,
    )
    db.add(log)
    await db.flush()

    return {
        "success": True,
        "website_id": website.id,
        "domain": website.domain,
        "site_title": data.site_title,
        "db_name": install_res["db_name"],
        "db_user": install_res["db_user"],
        "admin_username": data.admin_username,
        "configured_via_cli": install_res.get("configured_via_cli", False),
        "url": install_res["url"],
        "message": f"WordPress successfully installed on '{data.domain}'",
    }


@router.get("/{website_id}")
async def get_website(
    website_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get website details."""
    result = await db.execute(select(Website).where(Website.id == website_id))
    website = result.scalar_one_or_none()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    if user.role != UserRole.ADMIN and website.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": website.id,
        "user_id": website.user_id,
        "name": website.name,
        "domain": website.domain,
        "site_type": website.site_type.value if hasattr(website.site_type, 'value') else website.site_type,
        "status": website.status.value if hasattr(website.status, 'value') else website.status,
        "document_root": website.document_root,
        "php_version": website.php_version,
        "proxy_port": website.proxy_port,
        "ssl_enabled": website.ssl_enabled,
        "force_https": website.force_https,
        "git_repo": website.git_repo,
        "git_branch": website.git_branch,
        "auto_deploy": website.auto_deploy,
        "description": website.description,
        "created_at": website.created_at.isoformat() if website.created_at else None,
        "updated_at": website.updated_at.isoformat() if website.updated_at else None,
    }


@router.delete("/{website_id}")
async def delete_website(
    website_id: int,
    remove_files: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a website and its Nginx configuration."""
    result = await db.execute(select(Website).where(Website.id == website_id))
    website = result.scalar_one_or_none()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    if user.role != UserRole.ADMIN and website.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Remove Nginx config
    await nginx_service.delete_website(website.domain, remove_files=remove_files)

    # Log and delete
    log = ActivityLog(
        user_id=user.id,
        action="website.delete",
        category="website",
        description=f"Deleted website '{website.domain}'",
        resource_type="website",
        resource_name=website.domain,
    )
    db.add(log)

    await db.delete(website)
    return {"message": f"Website '{website.domain}' deleted successfully"}


@router.post("/{website_id}/toggle")
async def toggle_website(
    website_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a website."""
    result = await db.execute(select(Website).where(Website.id == website_id))
    website = result.scalar_one_or_none()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    if user.role != UserRole.ADMIN and website.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if website.status == WebsiteStatus.ACTIVE:
        await nginx_service.disable_site(website.domain)
        website.status = WebsiteStatus.DISABLED
        action = "disabled"
    else:
        await nginx_service.enable_site(website.domain)
        await nginx_service.reload()
        website.status = WebsiteStatus.ACTIVE
        action = "enabled"

    await db.flush()
    return {"message": f"Website '{website.domain}' {action}", "status": action}
