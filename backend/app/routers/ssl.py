"""
SSL Certificate API routes.
Issues Let's Encrypt certificates, manages website SSL, and handles renewals.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User, UserRole
from app.models.ssl_cert import SSLCertificate, CertType, CertStatus
from app.models.domain import Domain
from app.models.website import Website
from app.models.activity_log import ActivityLog
from app.schemas.ssl import SSLIssueRequest, SSLUploadRequest
from app.services.ssl_service import ssl_service
from app.services.nginx_service import nginx_service

router = APIRouter(prefix="/api/ssl", tags=["SSL/TLS"])


@router.get("")
async def list_certificates(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all SSL certificates."""
    result = await db.execute(
        select(SSLCertificate).order_by(SSLCertificate.created_at.desc())
    )
    certs = result.scalars().all()

    return [
        {
            "id": c.id, "domain_name": c.domain_name,
            "cert_type": c.cert_type.value if hasattr(c.cert_type, 'value') else c.cert_type,
            "status": c.status.value if hasattr(c.status, 'value') else c.status,
            "issuer": c.issuer,
            "issued_at": c.issued_at.isoformat() if c.issued_at else None,
            "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            "auto_renew": c.auto_renew,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in certs
    ]


@router.post("/issue", status_code=status.HTTP_201_CREATED)
async def issue_certificate(
    data: SSLIssueRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Issue a Let's Encrypt certificate for a domain.

    Works with both website domains and standalone domain records.
    """
    domain_name = data.domain_name.strip().lower()
    website_id = data.website_id
    domain_id = None

    # Check if an active certificate already exists for this domain
    existing_cert = await db.execute(
        select(SSLCertificate).where(
            SSLCertificate.domain_name == domain_name,
            SSLCertificate.status == CertStatus.ACTIVE,
        )
    )
    if existing_cert.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"An active SSL certificate already exists for '{domain_name}'. Remove it first to re-issue.",
        )

    # Try to find the domain in the domains table
    domain_result = await db.execute(
        select(Domain).where(Domain.name == domain_name)
    )
    domain = domain_result.scalar_one_or_none()
    if domain:
        domain_id = domain.id

    # If no domain record exists, try to resolve it from a website
    if not domain_id:
        website_result = await db.execute(
            select(Website).where(Website.domain == domain_name)
        )
        website = website_result.scalar_one_or_none()
        if website:
            website_id = website.id
            # Auto-create a domain record so the FK constraint is satisfied
            domain = Domain(
                user_id=user.id,
                name=domain_name,
                status="active",
            )
            db.add(domain)
            await db.flush()
            domain_id = domain.id
        else:
            # Neither website nor domain record exists — allow manual issuance with an auto-created domain
            domain = Domain(
                user_id=user.id,
                name=domain_name,
                status="active",
            )
            db.add(domain)
            await db.flush()
            domain_id = domain.id

    # Issue certificate via certbot
    result = await ssl_service.issue_letsencrypt(domain_name, user.email)
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "SSL issuance failed. Make sure the domain points to this server and port 80 is open."),
        )

    # Save certificate record
    cert = SSLCertificate(
        domain_id=domain_id,
        website_id=website_id,
        domain_name=domain_name,
        cert_type=CertType.LETS_ENCRYPT,
        status=CertStatus.ACTIVE,
        cert_path=result["cert_path"],
        key_path=result["key_path"],
        chain_path=result.get("chain_path"),
        issuer="Let's Encrypt",
        issued_at=datetime.utcnow(),
        auto_renew=data.auto_renew,
    )
    db.add(cert)

    # Find the website to get its site_type and php_version for correct SSL template
    site_type = "php"
    php_version = "8.2"
    proxy_port = None
    proxy_address = "127.0.0.1"

    if website_id:
        ws_result = await db.execute(select(Website).where(Website.id == website_id))
        ws = ws_result.scalar_one_or_none()
    else:
        ws_result = await db.execute(select(Website).where(Website.domain == domain_name))
        ws = ws_result.scalar_one_or_none()

    if ws:
        site_type = ws.site_type.value if hasattr(ws.site_type, 'value') else ws.site_type
        php_version = ws.php_version or "8.2"
        proxy_port = ws.proxy_port
        proxy_address = ws.proxy_address or "127.0.0.1"
        # Update website record to reflect SSL is enabled
        ws.ssl_enabled = True
        ws.force_https = True

    # Update Nginx config with SSL
    await nginx_service.update_ssl_config(
        domain_name,
        result["cert_path"],
        result["key_path"],
        result.get("chain_path"),
        force_https=True,
        site_type=site_type,
        php_version=php_version,
        proxy_port=proxy_port,
        proxy_address=proxy_address,
    )

    log = ActivityLog(
        user_id=user.id, action="ssl.issue", category="ssl",
        description=f"Issued Let's Encrypt SSL certificate for '{domain_name}'",
        resource_type="ssl", resource_name=domain_name,
    )
    db.add(log)

    await db.commit()
    return {"success": True, "message": f"SSL certificate issued for '{domain_name}'"}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_custom_certificate(
    data: SSLUploadRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and apply a custom SSL certificate for a website or domain."""
    domain_name = data.domain_name.strip().lower()
    website_id = data.website_id
    domain_id = None

    # Try domain lookup
    domain_result = await db.execute(select(Domain).where(Domain.name == domain_name))
    domain = domain_result.scalar_one_or_none()
    if domain:
        domain_id = domain.id
    else:
        # Create domain record if missing
        domain = Domain(user_id=user.id, name=domain_name, status="active")
        db.add(domain)
        await db.flush()
        domain_id = domain.id

    result = await ssl_service.upload_certificate(
        domain=domain_name,
        cert_content=data.certificate,
        key_content=data.private_key,
        chain_content=data.chain,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail="Failed to save custom certificate")

    # Store certificate record
    cert = SSLCertificate(
        domain_id=domain_id,
        website_id=website_id,
        domain_name=domain_name,
        cert_type=CertType.CUSTOM,
        status=CertStatus.ACTIVE,
        cert_path=result["cert_path"],
        key_path=result["key_path"],
        chain_path=result.get("chain_path"),
        issuer="Custom Certificate",
        issued_at=datetime.utcnow(),
        auto_renew=False,
    )
    db.add(cert)

    # Get website info for Nginx SSL template
    site_type = "php"
    php_version = "8.2"
    proxy_port = None
    proxy_address = "127.0.0.1"

    ws_result = await db.execute(select(Website).where(Website.domain == domain_name))
    ws = ws_result.scalar_one_or_none()
    if ws:
        site_type = ws.site_type.value if hasattr(ws.site_type, 'value') else ws.site_type
        php_version = ws.php_version or "8.2"
        proxy_port = ws.proxy_port
        proxy_address = ws.proxy_address or "127.0.0.1"
        ws.ssl_enabled = True
        ws.force_https = True

    await nginx_service.update_ssl_config(
        domain_name,
        result["cert_path"],
        result["key_path"],
        result.get("chain_path"),
        force_https=True,
        site_type=site_type,
        php_version=php_version,
        proxy_port=proxy_port,
        proxy_address=proxy_address,
    )

    log = ActivityLog(
        user_id=user.id,
        action="ssl.upload",
        category="ssl",
        description=f"Uploaded custom SSL certificate for '{domain_name}'",
        resource_type="ssl",
        resource_name=domain_name,
    )
    db.add(log)
    await db.commit()

    return {"success": True, "message": f"Custom SSL certificate installed for '{domain_name}'"}


@router.post("/renew")
async def renew_certificates(user: User = Depends(require_admin)):
    """Renew all Let's Encrypt certificates that are due."""
    result = await ssl_service.renew_certificates()
    if result.get("success"):
        return {"success": True, "message": "Certificate renewal completed successfully", "output": result.get("output")}
    return {"success": False, "message": "Renewal encountered issues", "output": result.get("output")}


@router.delete("/{cert_id}")
async def delete_certificate(
    cert_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a certificate and revert site to HTTP."""
    result = await db.execute(select(SSLCertificate).where(SSLCertificate.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    domain_name = cert.domain_name

    # Revoke and delete from disk
    await ssl_service.delete_certificate(domain_name)

    # Revert website SSL status
    ws_result = await db.execute(select(Website).where(Website.domain == domain_name))
    ws = ws_result.scalar_one_or_none()
    if ws:
        ws.ssl_enabled = False
        ws.force_https = False
        # Regenerate the HTTP-only vhost config
        site_type = ws.site_type.value if hasattr(ws.site_type, 'value') else ws.site_type
        await nginx_service.create_website(
            domain=domain_name,
            site_type=site_type,
            php_version=ws.php_version or "8.2",
            proxy_port=ws.proxy_port,
            proxy_address=ws.proxy_address or "127.0.0.1",
        )

    # Log and delete record
    log = ActivityLog(
        user_id=user.id, action="ssl.delete", category="ssl",
        description=f"Removed SSL certificate for '{domain_name}'",
        resource_type="ssl", resource_name=domain_name,
    )
    db.add(log)
    await db.delete(cert)
    await db.commit()

    return {"success": True, "message": f"Certificate for '{domain_name}' deleted"}
