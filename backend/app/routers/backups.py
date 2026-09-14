"""
Backup and restore API routes.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User, UserRole
from app.models.backup import Backup, BackupType, BackupStatus
from app.models.website import Website
from app.models.database_model import Database
from app.models.activity_log import ActivityLog
from app.schemas.backup import BackupCreate
from app.services.backup_service import backup_service

router = APIRouter(prefix="/api/backups", tags=["Backups"])


@router.get("")
async def list_backups(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all backups."""
    query = select(Backup)
    if user.role != UserRole.ADMIN:
        query = query.where(Backup.user_id == user.id)

    result = await db.execute(query.order_by(Backup.created_at.desc()))
    backups = result.scalars().all()

    return [
        {
            "id": b.id,
            "backup_type": b.backup_type.value if b.backup_type else "full",
            "status": b.status.value if b.status else "pending",
            "website_id": b.website_id,
            "database_id": b.database_id,
            "filename": b.filename,
            "filepath": b.filepath,
            "size_bytes": b.size_bytes,
            "description": b.description,
            "error_message": b.error_message,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "completed_at": b.completed_at.isoformat() if b.completed_at else None,
        }
        for b in backups
    ]


@router.get("/storage")
async def get_storage_info(user: User = Depends(get_current_user)):
    """Get backup storage usage stats."""
    return await backup_service.get_storage_info()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_backup(
    data: BackupCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new backup. Runs asynchronously in the background."""
    # Validate backup type
    try:
        backup_type = BackupType(data.backup_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid backup type. Use: full, website, database, files")

    # Create backup record
    backup = Backup(
        user_id=user.id,
        backup_type=backup_type,
        status=BackupStatus.IN_PROGRESS,
        website_id=data.website_id,
        database_id=data.database_id,
        description=data.description,
    )
    db.add(backup)

    log = ActivityLog(
        user_id=user.id,
        action="backup.create",
        category="backup",
        description=f"Started {data.backup_type} backup",
        resource_type="backup",
    )
    db.add(log)

    await db.flush()
    await db.refresh(backup)
    backup_id = backup.id

    # Run backup in background
    asyncio.create_task(_run_backup(backup_id, data, user))

    return {"id": backup_id, "status": "in_progress", "message": "Backup started"}


async def _run_backup(backup_id: int, data: BackupCreate, user: User):
    """Background task to execute the backup."""
    from app.database import async_session

    async with async_session() as db:
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()
        if not backup:
            return

        try:
            backup_type = BackupType(data.backup_type)

            if backup_type == BackupType.FULL:
                result = await backup_service.create_full_backup(user.id)

            elif backup_type == BackupType.WEBSITE:
                if not data.website_id:
                    raise ValueError("website_id required for website backup")
                ws_result = await db.execute(select(Website).where(Website.id == data.website_id))
                website = ws_result.scalar_one_or_none()
                if not website:
                    raise ValueError("Website not found")
                # Find associated database
                db_name = None
                if website.id:
                    db_result = await db.execute(
                        select(Database).where(Database.website_id == website.id)
                    )
                    assoc_db = db_result.scalar_one_or_none()
                    if assoc_db:
                        db_name = assoc_db.name
                result = await backup_service.create_website_backup(
                    website.domain, website.document_root, db_name
                )

            elif backup_type == BackupType.DATABASE:
                if not data.database_id:
                    raise ValueError("database_id required for database backup")
                db_result = await db.execute(select(Database).where(Database.id == data.database_id))
                database = db_result.scalar_one_or_none()
                if not database:
                    raise ValueError("Database not found")
                result = await backup_service.create_database_backup(database.name)

            else:
                raise ValueError(f"Unsupported backup type: {data.backup_type}")

            if result.get("success"):
                backup.status = BackupStatus.COMPLETED
                backup.filename = result.get("filename")
                backup.filepath = result.get("filepath")
                backup.size_bytes = result.get("size_bytes", 0)
                backup.completed_at = datetime.utcnow()
            else:
                backup.status = BackupStatus.FAILED
                backup.error_message = result.get("error", "Unknown error")

        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)

        await db.commit()


@router.get("/{backup_id}/download")
async def download_backup(
    backup_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a backup file."""
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    if user.role != UserRole.ADMIN and backup.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if backup.status != BackupStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Backup not completed")
    if not backup.filepath:
        raise HTTPException(status_code=400, detail="Backup file path missing")

    return FileResponse(
        path=backup.filepath,
        filename=backup.filename,
        media_type="application/gzip",
    )


@router.post("/{backup_id}/restore")
async def restore_backup(
    backup_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Restore from a backup. Admin only."""
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    if backup.status != BackupStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot restore — backup not completed")
    if not backup.filepath:
        raise HTTPException(status_code=400, detail="Backup file path missing")

    if backup.backup_type == BackupType.DATABASE:
        if not backup.database_id:
            raise HTTPException(status_code=400, detail="No database associated with this backup")
        db_result = await db.execute(select(Database).where(Database.id == backup.database_id))
        database = db_result.scalar_one_or_none()
        if not database:
            raise HTTPException(status_code=404, detail="Original database not found")
        restore_result = await backup_service.restore_database_backup(backup.filepath, database.name)
    else:
        restore_result = await backup_service.restore_full_backup(backup.filepath)

    if not restore_result.get("success"):
        raise HTTPException(status_code=500, detail=restore_result.get("error", "Restore failed"))

    log = ActivityLog(
        user_id=user.id,
        action="backup.restore",
        category="backup",
        description=f"Restored from backup #{backup_id} ({backup.backup_type.value})",
        resource_type="backup",
        resource_id=backup_id,
    )
    db.add(log)

    return {"message": "Backup restored successfully"}


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a backup and its file."""
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    if user.role != UserRole.ADMIN and backup.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete file
    if backup.filepath:
        await backup_service.delete_backup(backup.filepath)

    log = ActivityLog(
        user_id=user.id,
        action="backup.delete",
        category="backup",
        description=f"Deleted backup '{backup.filename}'",
        resource_type="backup",
    )
    db.add(log)

    await db.delete(backup)
    return {"message": "Backup deleted"}
