"""
Service management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import require_admin
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.services.service_manager import service_manager
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/services", tags=["Services"])


@router.get("")
async def list_services(user: User = Depends(require_admin)):
    """List all managed services with status."""
    return await service_manager.list_services()


@router.post("/{service_name}/start")
async def start_service(
    service_name: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Start a service."""
    try:
        result = await service_manager.start_service(service_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to start service"))

    db.add(ActivityLog(
        user_id=user.id, action="service.start", category="service",
        description=f"Started service '{service_name}'",
        resource_type="service", resource_name=service_name,
    ))

    return {"message": f"Service '{service_name}' started"}


@router.post("/{service_name}/stop")
async def stop_service(
    service_name: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Stop a service."""
    try:
        result = await service_manager.stop_service(service_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to stop service"))

    db.add(ActivityLog(
        user_id=user.id, action="service.stop", category="service",
        description=f"Stopped service '{service_name}'",
        resource_type="service", resource_name=service_name,
    ))

    return {"message": f"Service '{service_name}' stopped"}


@router.post("/{service_name}/restart")
async def restart_service(
    service_name: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Restart a service."""
    try:
        result = await service_manager.restart_service(service_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to restart service"))

    db.add(ActivityLog(
        user_id=user.id, action="service.restart", category="service",
        description=f"Restarted service '{service_name}'",
        resource_type="service", resource_name=service_name,
    ))

    return {"message": f"Service '{service_name}' restarted"}


@router.post("/{service_name}/enable")
async def enable_service(
    service_name: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable a service to start on boot."""
    try:
        result = await service_manager.enable_service(service_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to enable service"))

    return {"message": f"Service '{service_name}' enabled on boot"}


@router.post("/{service_name}/disable")
async def disable_service(
    service_name: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Disable a service from starting on boot."""
    try:
        result = await service_manager.disable_service(service_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to disable service"))

    return {"message": f"Service '{service_name}' disabled from boot"}
