"""
FTP (Pure-FTPd) API routes.
Provides optional installation, service management, and virtual user configuration.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_admin
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.schemas.ftp import FTPAccountCreate, FTPAccountUpdate, FTPAccountResponse
from app.services.ftp_service import ftp_service

router = APIRouter(prefix="/api/ftp", tags=["FTP"])


@router.get("/status")
async def ftp_status(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Check Pure-FTPd installation, service status, and account count."""
    return await ftp_service.get_status(db)


@router.post("/install")
async def install_ftp(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Install and configure Pure-FTPd with virtual user authentication."""
    status = await ftp_service.get_status()
    if status["installed"]:
        raise HTTPException(status_code=400, detail="Pure-FTPd is already installed")

    result = await ftp_service.install()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Pure-FTPd installation failed"))

    db.add(ActivityLog(
        user_id=user.id,
        action="ftp.install",
        category="ftp",
        description="Installed and configured Pure-FTPd server",
        resource_type="service",
        resource_name="pure-ftpd",
    ))
    return {"message": "Pure-FTPd installed and started successfully"}


@router.post("/uninstall")
async def uninstall_ftp(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Stop and uninstall Pure-FTPd."""
    result = await ftp_service.uninstall()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to uninstall Pure-FTPd"))

    db.add(ActivityLog(
        user_id=user.id,
        action="ftp.uninstall",
        category="ftp",
        description="Uninstalled Pure-FTPd server",
        resource_type="service",
        resource_name="pure-ftpd",
    ))
    return {"message": "Pure-FTPd uninstalled"}


@router.post("/service/{action}")
async def ftp_service_action(
    action: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Start, stop, or restart the Pure-FTPd service."""
    result = await ftp_service.service_action(action)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", f"Failed to {action} pure-ftpd"))

    db.add(ActivityLog(
        user_id=user.id,
        action=f"ftp.service.{action}",
        category="ftp",
        description=f"{action.capitalize()}ed Pure-FTPd service",
        resource_type="service",
        resource_name="pure-ftpd",
    ))
    return {"message": f"Pure-FTPd {action}ed"}


@router.get("/accounts", response_model=list[FTPAccountResponse])
async def list_ftp_accounts(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all registered virtual FTP accounts."""
    return await ftp_service.list_accounts(db)


@router.post("/accounts", response_model=FTPAccountResponse)
async def create_ftp_account(
    data: FTPAccountCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new virtual FTP account in PureDB and record in database."""
    try:
        account = await ftp_service.create_account(
            db=db,
            user_id=user.id,
            username=data.username,
            password=data.password,
            directory=data.directory,
            quota_mb=data.quota_mb or 0,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating FTP account: {str(e)}")

    db.add(ActivityLog(
        user_id=user.id,
        action="ftp.account.create",
        category="ftp",
        description=f"Created FTP account '{data.username}' for '{data.directory}'",
        resource_type="ftp_account",
        resource_name=data.username,
    ))
    return account


@router.put("/accounts/{account_id}", response_model=FTPAccountResponse)
async def update_ftp_account(
    account_id: int,
    data: FTPAccountUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update password, directory, quota, or status for an existing FTP account."""
    try:
        account = await ftp_service.update_account(
            db=db,
            account_id=account_id,
            password=data.password,
            directory=data.directory,
            quota_mb=data.quota_mb,
            status=data.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating FTP account: {str(e)}")

    db.add(ActivityLog(
        user_id=user.id,
        action="ftp.account.update",
        category="ftp",
        description=f"Updated FTP account '{account.username}'",
        resource_type="ftp_account",
        resource_name=account.username,
    ))
    return account


@router.delete("/accounts/{account_id}")
async def delete_ftp_account(
    account_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an FTP account from PureDB and database."""
    success = await ftp_service.delete_account(db, account_id)
    if not success:
        raise HTTPException(status_code=404, detail="FTP account not found")

    db.add(ActivityLog(
        user_id=user.id,
        action="ftp.account.delete",
        category="ftp",
        description=f"Deleted FTP account ID {account_id}",
        resource_type="ftp_account",
        resource_name=str(account_id),
    ))
    return {"message": "FTP account deleted"}
