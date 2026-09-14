"""
Cron job management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole
from app.models.cron_job import CronJob
from app.models.activity_log import ActivityLog
from app.schemas.backup import CronJobCreate, CronJobUpdate
from app.services.cron_service import cron_service

router = APIRouter(prefix="/api/cron", tags=["Cron Jobs"])


@router.get("")
async def list_cron_jobs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all cron jobs."""
    query = select(CronJob)
    if user.role != UserRole.ADMIN:
        query = query.where(CronJob.user_id == user.id)

    result = await db.execute(query.order_by(CronJob.created_at.desc()))
    jobs = result.scalars().all()

    return [
        {
            "id": j.id,
            "schedule": j.schedule,
            "command": j.command,
            "description": j.description or cron_service.describe_schedule(j.schedule),
            "enabled": j.enabled,
            "last_run": j.last_run.isoformat() if j.last_run else None,
            "last_status": j.last_status,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]


@router.get("/presets")
async def get_presets(user: User = Depends(get_current_user)):
    """Get common cron schedule presets."""
    return cron_service.get_presets()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_cron_job(
    data: CronJobCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new cron job."""
    if not cron_service.validate_schedule(data.schedule):
        raise HTTPException(status_code=400, detail="Invalid cron schedule expression")

    # Add to system crontab
    system_user = user.system_username or "root"
    if data.enabled:
        result = await cron_service.add_to_crontab(system_user, data.schedule, data.command)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to add cron job"))

    # Save to panel DB
    job = CronJob(
        user_id=user.id,
        schedule=data.schedule,
        command=data.command,
        description=data.description,
        enabled=data.enabled,
    )
    db.add(job)

    log = ActivityLog(
        user_id=user.id,
        action="cron.create",
        category="cron",
        description=f"Created cron job: {data.schedule} {data.command[:50]}",
        resource_type="cron_job",
    )
    db.add(log)

    await db.flush()
    await db.refresh(job)

    return {"id": job.id, "schedule": job.schedule, "message": "Cron job created successfully"}


@router.put("/{job_id}")
async def update_cron_job(
    job_id: int,
    data: CronJobUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a cron job."""
    result = await db.execute(select(CronJob).where(CronJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Cron job not found")
    if user.role != UserRole.ADMIN and job.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    new_schedule = data.schedule or job.schedule
    new_command = data.command or job.command

    if data.schedule and not cron_service.validate_schedule(data.schedule):
        raise HTTPException(status_code=400, detail="Invalid cron schedule expression")

    # Update system crontab
    system_user = user.system_username or "root"
    if job.enabled:
        await cron_service.remove_from_crontab(system_user, job.schedule, job.command)

    new_enabled = data.enabled if data.enabled is not None else job.enabled
    if new_enabled:
        await cron_service.add_to_crontab(system_user, new_schedule, new_command)

    # Update DB
    if data.schedule is not None:
        job.schedule = data.schedule
    if data.command is not None:
        job.command = data.command
    if data.description is not None:
        job.description = data.description
    if data.enabled is not None:
        job.enabled = data.enabled

    log = ActivityLog(
        user_id=user.id,
        action="cron.update",
        category="cron",
        description=f"Updated cron job #{job_id}",
        resource_type="cron_job",
        resource_id=job_id,
    )
    db.add(log)

    return {"message": "Cron job updated successfully"}


@router.delete("/{job_id}")
async def delete_cron_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a cron job."""
    result = await db.execute(select(CronJob).where(CronJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Cron job not found")
    if user.role != UserRole.ADMIN and job.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Remove from system crontab
    system_user = user.system_username or "root"
    if job.enabled:
        await cron_service.remove_from_crontab(system_user, job.schedule, job.command)

    log = ActivityLog(
        user_id=user.id,
        action="cron.delete",
        category="cron",
        description=f"Deleted cron job: {job.schedule} {job.command[:50]}",
        resource_type="cron_job",
    )
    db.add(log)

    await db.delete(job)
    return {"message": "Cron job deleted"}


@router.post("/{job_id}/toggle")
async def toggle_cron_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a cron job enabled/disabled."""
    result = await db.execute(select(CronJob).where(CronJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Cron job not found")
    if user.role != UserRole.ADMIN and job.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    system_user = user.system_username or "root"

    if job.enabled:
        # Disable: remove from crontab
        await cron_service.remove_from_crontab(system_user, job.schedule, job.command)
        job.enabled = False
    else:
        # Enable: add to crontab
        await cron_service.add_to_crontab(system_user, job.schedule, job.command)
        job.enabled = True

    return {"enabled": job.enabled, "message": f"Cron job {'enabled' if job.enabled else 'disabled'}"}
