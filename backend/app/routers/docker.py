"""
Docker management API routes.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.middleware.auth import require_admin
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.services.docker_service import docker_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/docker", tags=["Docker"])


@router.get("/status")
async def docker_status(user: User = Depends(require_admin)):
    """Check Docker installation status."""
    return await docker_service.get_status()


@router.post("/install")
async def install_docker(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Install Docker Engine."""
    status = await docker_service.get_status()
    if status["installed"]:
        raise HTTPException(status_code=400, detail="Docker is already installed")

    result = await docker_service.install_docker()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Docker installation failed"))

    db.add(ActivityLog(
        user_id=user.id, action="docker.install", category="docker",
        description="Installed Docker Engine", resource_type="docker",
    ))
    return {"message": "Docker installed successfully"}


@router.get("/containers")
async def list_containers(user: User = Depends(require_admin)):
    """List all Docker containers."""
    return await docker_service.list_containers()


@router.post("/containers")
async def create_container(
    image: str,
    name: Optional[str] = None,
    ports: Optional[str] = None,
    volumes: Optional[str] = None,
    env_vars: Optional[str] = None,
    restart_policy: str = "unless-stopped",
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create and start a new container."""
    result = await docker_service.create_container(
        image=image, name=name, ports=ports,
        volumes=volumes, env_vars=env_vars,
        restart_policy=restart_policy,
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to create container"))

    db.add(ActivityLog(
        user_id=user.id, action="docker.container.create", category="docker",
        description=f"Created container from {image}" + (f" as '{name}'" if name else ""),
        resource_type="container", resource_name=name or image,
    ))
    return result


@router.post("/containers/{container_id}/{action}")
async def container_action(
    container_id: str,
    action: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Start, stop, restart, or remove a container."""
    if action not in ("start", "stop", "restart", "remove"):
        raise HTTPException(status_code=400, detail="Invalid action")

    result = await docker_service.container_action(container_id, action)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", f"Failed to {action} container"))

    db.add(ActivityLog(
        user_id=user.id, action=f"docker.container.{action}", category="docker",
        description=f"{action.capitalize()}ed container {container_id}",
        resource_type="container", resource_name=container_id,
    ))
    return {"message": f"Container {action}ed"}


@router.get("/containers/{container_id}/logs")
async def container_logs(
    container_id: str,
    tail: int = Query(100, ge=10, le=5000),
    user: User = Depends(require_admin),
):
    """Get container logs."""
    logs = await docker_service.get_container_logs(container_id, tail)
    return {"logs": logs}


@router.get("/images")
async def list_images(user: User = Depends(require_admin)):
    """List Docker images."""
    return await docker_service.list_images()


@router.post("/images/pull")
async def pull_image(
    image: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pull a Docker image."""
    result = await docker_service.pull_image(image)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to pull image"))

    db.add(ActivityLog(
        user_id=user.id, action="docker.image.pull", category="docker",
        description=f"Pulled image {image}", resource_type="image", resource_name=image,
    ))
    return {"message": f"Image {image} pulled successfully"}


@router.delete("/images/{image_id}")
async def remove_image(
    image_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a Docker image."""
    result = await docker_service.remove_image(image_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to remove image"))

    db.add(ActivityLog(
        user_id=user.id, action="docker.image.remove", category="docker",
        description=f"Removed image {image_id}", resource_type="image",
    ))
    return {"message": "Image removed"}


@router.post("/uninstall")
async def uninstall_docker(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Uninstall Docker Engine and free resources."""
    result = await docker_service.uninstall_docker()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to uninstall Docker"))

    db.add(ActivityLog(
        user_id=user.id, action="docker.uninstall", category="docker",
        description="Uninstalled Docker Engine", resource_type="docker",
    ))
    return {"message": "Docker uninstalled successfully"}

