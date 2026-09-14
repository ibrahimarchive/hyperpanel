"""
PHP version management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.middleware.auth import require_admin
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.services.php_service import php_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/php", tags=["PHP"])


class ConfigUpdate(BaseModel):
    directives: dict


@router.get("/versions")
async def list_versions(user: User = Depends(require_admin)):
    """List installed PHP versions."""
    return await php_service.list_installed_versions()


@router.post("/versions/install")
async def install_version(
    version: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Install a PHP version."""
    result = await php_service.install_version(version)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Installation failed"))

    db.add(ActivityLog(
        user_id=user.id, action="php.install", category="php",
        description=f"Installed PHP {version}", resource_type="php", resource_name=version,
    ))
    return {"message": f"PHP {version} installed successfully"}


@router.delete("/versions/{version}")
async def remove_version(
    version: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a PHP version."""
    result = await php_service.remove_version(version)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Removal failed"))

    db.add(ActivityLog(
        user_id=user.id, action="php.remove", category="php",
        description=f"Removed PHP {version}", resource_type="php", resource_name=version,
    ))
    return {"message": f"PHP {version} removed"}


@router.get("/versions/{version}/extensions")
async def list_extensions(version: str, user: User = Depends(require_admin)):
    """List extensions for a PHP version."""
    return await php_service.list_extensions(version)


@router.post("/versions/{version}/extensions/toggle")
async def toggle_extension(
    version: str,
    extension: str,
    enable: bool = True,
    user: User = Depends(require_admin),
):
    """Enable or disable a PHP extension."""
    result = await php_service.toggle_extension(version, extension, enable)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to toggle extension")
    return {"message": f"Extension {extension} {'enabled' if enable else 'disabled'}"}


@router.get("/versions/{version}/config")
async def get_config(version: str, user: User = Depends(require_admin)):
    """Get php.ini configuration."""
    return await php_service.get_config(version)


@router.put("/versions/{version}/config")
async def update_config(
    version: str,
    data: ConfigUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update php.ini configuration."""
    result = await php_service.update_config(version, data.directives)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to update configuration")

    db.add(ActivityLog(
        user_id=user.id, action="php.config", category="php",
        description=f"Updated PHP {version} configuration", resource_type="php", resource_name=version,
    ))
    return {"message": f"PHP {version} configuration updated"}


@router.post("/versions/{version}/restart")
async def restart_fpm(version: str, user: User = Depends(require_admin)):
    """Restart PHP-FPM."""
    result = await php_service.restart_fpm(version)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to restart PHP-FPM")
    return {"message": f"PHP {version}-FPM restarted"}
