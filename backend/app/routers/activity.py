"""
Activity / Audit log API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User, UserRole
from app.models.activity_log import ActivityLog

router = APIRouter(prefix="/api/activity", tags=["Activity Log"])


@router.get("")
async def list_activity(
    category: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List activity logs with filters and pagination."""
    query = select(ActivityLog)

    # Non-admins can only see their own logs
    if user.role != UserRole.ADMIN:
        query = query.where(ActivityLog.user_id == user.id)
    elif user_id:
        query = query.where(ActivityLog.user_id == user_id)

    if category:
        query = query.where(ActivityLog.category == category)
    if action:
        query = query.where(ActivityLog.action == action)
    if status:
        query = query.where(ActivityLog.status == status)
    if from_date:
        try:
            dt = datetime.fromisoformat(from_date)
            query = query.where(ActivityLog.created_at >= dt)
        except ValueError:
            pass
    if to_date:
        try:
            dt = datetime.fromisoformat(to_date)
            query = query.where(ActivityLog.created_at <= dt)
        except ValueError:
            pass

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    query = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "category": log.category,
                "description": log.description,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "ip_address": log.ip_address,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


@router.get("/stats")
async def activity_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get activity statistics grouped by category."""
    query = select(
        ActivityLog.category,
        func.count(ActivityLog.id).label("count"),
    )

    if user.role != UserRole.ADMIN:
        query = query.where(ActivityLog.user_id == user.id)

    query = query.group_by(ActivityLog.category)
    result = await db.execute(query)
    rows = result.all()

    stats = {row[0]: row[1] for row in rows}

    # Recent activity count (last 24h)
    from datetime import timedelta
    recent_query = select(func.count(ActivityLog.id)).where(
        ActivityLog.created_at >= datetime.utcnow() - timedelta(hours=24)
    )
    if user.role != UserRole.ADMIN:
        recent_query = recent_query.where(ActivityLog.user_id == user.id)
    recent_count = (await db.execute(recent_query)).scalar() or 0

    return {
        "by_category": stats,
        "recent_24h": recent_count,
        "total": sum(stats.values()),
    }


@router.get("/categories")
async def list_categories(user: User = Depends(get_current_user)):
    """List all available activity categories."""
    return [
        "auth", "website", "database", "domain", "dns",
        "ssl", "firewall", "file", "backup", "cron",
        "user", "docker", "service", "system",
    ]


@router.delete("/clear")
async def clear_old_logs(
    days: int = Query(90, ge=1, le=365),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Clear activity logs older than N days. Admin only."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(func.count(ActivityLog.id)).where(ActivityLog.created_at < cutoff)
    )
    count = result.scalar() or 0

    if count > 0:
        from sqlalchemy import delete
        await db.execute(
            delete(ActivityLog).where(ActivityLog.created_at < cutoff)
        )

    return {"deleted": count, "message": f"Cleared {count} log entries older than {days} days"}
