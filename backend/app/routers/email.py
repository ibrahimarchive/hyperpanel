"""
Email (BillionMail) API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import require_admin
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.services.billionmail_service import billionmail_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/email", tags=["Email"])


@router.get("/status")
async def email_status(user: User = Depends(require_admin)):
    """Check BillionMail status."""
    return await billionmail_service.get_status()


@router.post("/install")
async def install_email(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Install BillionMail."""
    status = await billionmail_service.get_status()
    if status["installed"]:
        raise HTTPException(status_code=400, detail="BillionMail is already installed")

    result = await billionmail_service.install()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Installation failed"))

    db.add(ActivityLog(
        user_id=user.id, action="email.install", category="email",
        description="Installed BillionMail", resource_type="email",
    ))
    return {"message": "BillionMail installed successfully"}


@router.post("/start")
async def start_email(user: User = Depends(require_admin)):
    """Start BillionMail."""
    result = await billionmail_service.start()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to start"))
    return {"message": "BillionMail started"}


@router.post("/stop")
async def stop_email(user: User = Depends(require_admin)):
    """Stop BillionMail."""
    result = await billionmail_service.stop()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to stop"))
    return {"message": "BillionMail stopped"}


@router.post("/restart")
async def restart_email(user: User = Depends(require_admin)):
    """Restart BillionMail."""
    result = await billionmail_service.restart()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to restart"))
    return {"message": "BillionMail restarted"}


@router.get("/credentials")
async def get_email_credentials(user: User = Depends(require_admin)):
    """Get default login credentials for BillionMail."""
    return await billionmail_service.get_credentials()


@router.post("/uninstall")
async def uninstall_email(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Uninstall BillionMail."""
    result = await billionmail_service.uninstall()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to uninstall")

    db.add(ActivityLog(
        user_id=user.id, action="email.uninstall", category="email",
        description="Uninstalled BillionMail", resource_type="email",
    ))
    return {"message": "BillionMail uninstalled"}
