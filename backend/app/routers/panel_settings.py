"""
Panel settings API routes for Network & Access, Panel SSL, and Authentication options.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User, UserRole
from app.models.activity_log import ActivityLog
from app.services.panel_settings_service import panel_settings_service
from app.services.auth_service import verify_password

router = APIRouter(prefix="/api/settings/panel", tags=["Panel Settings"])


class DomainUpdateRequest(BaseModel):
    domain: str


class PortUpdateRequest(BaseModel):
    port: int


class SSLToggleRequest(BaseModel):
    enabled: bool


class CustomSSLRequest(BaseModel):
    certificate: str
    private_key: str


class UsernameUpdateRequest(BaseModel):
    username: str
    password: str


@router.get("")
async def get_panel_settings(user: User = Depends(get_current_user)):
    """Get panel network, SSL, and authentication settings."""
    return panel_settings_service.get_all_settings(username=user.username)


@router.post("/domain")
async def update_panel_domain(
    data: DomainUpdateRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Set or remove the domain bound to the control panel."""
    result = await panel_settings_service.set_panel_domain(data.domain)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update domain"))

    log = ActivityLog(
        user_id=user.id,
        action="panel.update_domain",
        category="settings",
        description=f"Updated panel domain to '{data.domain}'",
        resource_type="system",
        resource_name="panel_domain",
    )
    db.add(log)
    await db.commit()

    return result


@router.post("/port")
async def update_panel_port(
    data: PortUpdateRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update panel listening port and configure firewall."""
    result = await panel_settings_service.set_panel_port(data.port)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Invalid port"))

    log = ActivityLog(
        user_id=user.id,
        action="panel.update_port",
        category="settings",
        description=f"Updated panel port to {data.port}",
        resource_type="system",
        resource_name="panel_port",
    )
    db.add(log)
    await db.commit()

    return result


@router.post("/ssl/toggle")
async def toggle_panel_ssl(
    data: SSLToggleRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Toggle panel SSL on or off."""
    info = await panel_settings_service.toggle_ssl(data.enabled)

    log = ActivityLog(
        user_id=user.id,
        action="panel.ssl_toggle",
        category="security",
        description=f"Panel SSL {'enabled' if data.enabled else 'disabled'}",
        resource_type="system",
        resource_name="panel_ssl",
    )
    db.add(log)
    await db.commit()

    return {"success": True, "ssl": info}


@router.post("/ssl/custom")
async def update_custom_ssl(
    data: CustomSSLRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Install custom PEM certificate & private key for the panel."""
    result = await panel_settings_service.set_custom_ssl(data.certificate, data.private_key)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Invalid certificate or key"))

    log = ActivityLog(
        user_id=user.id,
        action="panel.ssl_update",
        category="security",
        description="Installed custom SSL certificate for control panel",
        resource_type="system",
        resource_name="panel_ssl",
    )
    db.add(log)
    await db.commit()

    return result


@router.post("/ssl/self-signed")
async def generate_self_signed(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate and apply a 10-year self-signed SSL certificate for the panel."""
    current_settings = panel_settings_service._load_settings()
    domain = current_settings.get("panel_domain") or "127.0.0.1"
    info = panel_settings_service.generate_self_signed_cert(domain=domain)
    await panel_settings_service.sync_nginx_config()

    log = ActivityLog(
        user_id=user.id,
        action="panel.ssl_self_signed",
        category="security",
        description="Generated new 10-year self-signed certificate for panel",
        resource_type="system",
        resource_name="panel_ssl",
    )
    db.add(log)
    await db.commit()

    return {"success": True, "certificate": info, "message": "Self-signed certificate generated"}


@router.post("/username")
async def update_panel_username(
    data: UsernameUpdateRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Modify the panel administrator username."""
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_username = data.username.strip()
    if not new_username or len(new_username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    # Check conflict
    existing = await db.execute(select(User).where(User.username == new_username, User.id != user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Username '{new_username}' is already in use")

    old_username = user.username
    user.username = new_username

    log = ActivityLog(
        user_id=user.id,
        action="user.update_username",
        category="security",
        description=f"Changed panel username from '{old_username}' to '{new_username}'",
        resource_type="user",
        resource_name=new_username,
    )
    db.add(log)
    await db.commit()

    return {"success": True, "username": new_username, "message": f"Panel user changed to '{new_username}'"}
