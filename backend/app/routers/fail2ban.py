"""
Fail2Ban management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.middleware.auth import require_admin
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.services.fail2ban_service import fail2ban_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/fail2ban", tags=["Fail2Ban"])


class BanRequest(BaseModel):
    ip: str


@router.get("/status")
async def fail2ban_status(user: User = Depends(require_admin)):
    """Check Fail2Ban installation status."""
    return await fail2ban_service.get_status()


@router.post("/install")
async def install_fail2ban(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Install Fail2Ban."""
    status = await fail2ban_service.get_status()
    if status["installed"]:
        raise HTTPException(status_code=400, detail="Fail2Ban is already installed")

    result = await fail2ban_service.install()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Installation failed"))

    db.add(ActivityLog(
        user_id=user.id, action="fail2ban.install", category="security",
        description="Installed Fail2Ban", resource_type="fail2ban",
    ))
    return {"message": "Fail2Ban installed and started"}


@router.get("/jails")
async def list_jails(user: User = Depends(require_admin)):
    """List all Fail2Ban jails."""
    return await fail2ban_service.list_jails()


@router.get("/jails/{jail_name}")
async def jail_status(jail_name: str, user: User = Depends(require_admin)):
    """Get detailed status of a jail."""
    info = await fail2ban_service.get_jail_status(jail_name)
    if not info:
        raise HTTPException(status_code=404, detail="Jail not found")
    return info


@router.post("/jails/{jail_name}/ban")
async def ban_ip(
    jail_name: str,
    data: BanRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually ban an IP in a jail."""
    result = await fail2ban_service.ban_ip(jail_name, data.ip)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to ban IP"))

    db.add(ActivityLog(
        user_id=user.id, action="fail2ban.ban", category="security",
        description=f"Banned {data.ip} in jail '{jail_name}'",
        resource_type="fail2ban", resource_name=jail_name,
    ))
    return {"message": f"IP {data.ip} banned in {jail_name}"}


@router.post("/jails/{jail_name}/unban")
async def unban_ip(
    jail_name: str,
    data: BanRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Unban an IP from a jail."""
    result = await fail2ban_service.unban_ip(jail_name, data.ip)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to unban IP"))

    db.add(ActivityLog(
        user_id=user.id, action="fail2ban.unban", category="security",
        description=f"Unbanned {data.ip} from jail '{jail_name}'",
        resource_type="fail2ban", resource_name=jail_name,
    ))
    return {"message": f"IP {data.ip} unbanned from {jail_name}"}
