"""
Dashboard API routes.
Provides system stats, services status, and activity logs.
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.website import Website
from app.models.domain import Domain
from app.models.database_model import Database
from app.models.activity_log import ActivityLog
from app.services.system_service import (
    get_cpu_stats, get_memory_stats, get_disk_stats,
    get_network_stats, get_system_info, get_services_status,
    get_process_list,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full dashboard statistics."""
    # System stats
    cpu = get_cpu_stats()
    memory = get_memory_stats()
    disk = get_disk_stats()
    network = get_network_stats()
    system_info = get_system_info()
    services = await get_services_status()

    # Resource counts
    websites_count = (await db.execute(select(func.count(Website.id)))).scalar() or 0
    databases_count = (await db.execute(select(func.count(Database.id)))).scalar() or 0
    domains_count = (await db.execute(select(func.count(Domain.id)))).scalar() or 0
    users_count = (await db.execute(select(func.count(User.id)))).scalar() or 0

    return {
        "cpu": cpu.model_dump(),
        "memory": memory.model_dump(),
        "disk": disk.model_dump(),
        "network": network.model_dump(),
        "system_info": system_info.model_dump(),
        "services": [s.model_dump() for s in services],
        "websites_count": websites_count,
        "databases_count": databases_count,
        "domains_count": domains_count,
        "users_count": users_count,
    }


@router.get("/activity")
async def get_recent_activity(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    """Get recent activity logs."""
    result = await db.execute(
        select(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "action": log.action,
            "category": log.category,
            "description": log.description,
            "resource_type": log.resource_type,
            "resource_name": log.resource_name,
            "status": log.status,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/processes")
async def get_processes(user: User = Depends(get_current_user)):
    """Get top processes by CPU usage."""
    return get_process_list()
