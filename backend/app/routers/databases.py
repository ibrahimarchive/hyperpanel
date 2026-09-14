"""
Database management API routes.
"""

import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole
from app.models.database_model import Database, DatabaseUser
from app.models.activity_log import ActivityLog
from app.schemas.database import DatabaseCreate, DatabaseUserCreate
from app.services.database_service import database_service

router = APIRouter(prefix="/api/databases", tags=["Databases"])


@router.get("")
async def list_databases(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all databases."""
    query = select(Database)
    if user.role != UserRole.ADMIN:
        query = query.where(Database.user_id == user.id)

    result = await db.execute(query.order_by(Database.created_at.desc()))
    databases = result.scalars().all()

    return [
        {
            "id": d.id,
            "name": d.name,
            "charset": d.charset,
            "collation": d.collation,
            "size_bytes": d.size_bytes,
            "website_id": d.website_id,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in databases
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_database(
    data: DatabaseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new MySQL database."""
    # Create in MySQL
    result = await database_service.create_database(data.name, data.charset, data.collation)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to create database"))

    # Save to panel DB
    database = Database(
        user_id=user.id,
        name=data.name,
        charset=data.charset,
        collation=data.collation,
        website_id=data.website_id,
    )
    db.add(database)

    log = ActivityLog(
        user_id=user.id,
        action="database.create",
        category="database",
        description=f"Created database '{data.name}'",
        resource_type="database",
        resource_name=data.name,
    )
    db.add(log)

    await db.flush()
    await db.refresh(database)

    return {"id": database.id, "name": database.name, "message": "Database created successfully"}


@router.delete("/{database_id}")
async def delete_database(
    database_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a database."""
    result = await db.execute(select(Database).where(Database.id == database_id))
    database = result.scalar_one_or_none()

    if not database:
        raise HTTPException(status_code=404, detail="Database not found")
    if user.role != UserRole.ADMIN and database.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Drop from MySQL
    await database_service.drop_database(database.name)

    log = ActivityLog(
        user_id=user.id,
        action="database.delete",
        category="database",
        description=f"Deleted database '{database.name}'",
        resource_type="database",
        resource_name=database.name,
    )
    db.add(log)

    await db.delete(database)
    return {"message": f"Database '{database.name}' deleted"}


@router.get("/users")
async def list_database_users(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List database users."""
    query = select(DatabaseUser)
    if user.role != UserRole.ADMIN:
        query = query.where(DatabaseUser.user_id == user.id)

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "host": u.host,
            "database_ids": u.database_ids,
            "privileges": u.privileges,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_database_user(
    data: DatabaseUserCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a MySQL database user."""
    result = await database_service.create_user(data.username, data.password, data.host)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to create user"))

    # Grant privileges if database_ids specified
    if data.database_ids:
        for db_id_str in data.database_ids.split(","):
            db_id = int(db_id_str.strip())
            db_result = await db.execute(select(Database).where(Database.id == db_id))
            target_db = db_result.scalar_one_or_none()
            if target_db:
                await database_service.grant_privileges(
                    data.username, target_db.name, data.privileges, data.host
                )

    db_user = DatabaseUser(
        user_id=user.id,
        username=data.username,
        host=data.host,
        database_ids=data.database_ids,
        privileges=data.privileges,
    )
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)

    return {"id": db_user.id, "username": db_user.username, "message": "Database user created"}


@router.get("/{name}/export")
async def export_database_endpoint(
    name: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export a database as a .sql dump file."""
    db_result = await db.execute(select(Database).where(Database.name == name))
    database = db_result.scalar_one_or_none()
    if not database:
        all_dbs = await database_service.list_databases()
        if name not in all_dbs:
            raise HTTPException(status_code=404, detail=f"Database '{name}' not found")
        if user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
    elif user.role != UserRole.ADMIN and database.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    temp_fd, temp_path = tempfile.mkstemp(prefix=f"{name}_", suffix=".sql")
    os.close(temp_fd)

    res = await database_service.export_database(name, temp_path)
    if not res.get("success"):
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=res.get("error", "Database export failed"))

    background_tasks.add_task(os.remove, temp_path)
    return FileResponse(
        temp_path,
        media_type="application/sql",
        filename=f"{name}_backup.sql",
    )


@router.post("/{name}/import")
async def import_database_endpoint(
    name: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import a .sql file into an existing database."""
    db_result = await db.execute(select(Database).where(Database.name == name))
    database = db_result.scalar_one_or_none()
    if not database:
        all_dbs = await database_service.list_databases()
        if name not in all_dbs:
            raise HTTPException(status_code=404, detail=f"Database '{name}' not found")
        if user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
    elif user.role != UserRole.ADMIN and database.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    temp_fd, temp_path = tempfile.mkstemp(prefix="import_", suffix=".sql")
    try:
        content = await file.read()
        with os.fdopen(temp_fd, "wb") as f:
            f.write(content)

        res = await database_service.import_database(name, temp_path)
        if not res.get("success"):
            raise HTTPException(status_code=500, detail=res.get("error", "Failed to import SQL file"))

        log = ActivityLog(
            user_id=user.id,
            action="database.import",
            category="database",
            description=f"Imported SQL file '{file.filename}' into database '{name}'",
            resource_type="database",
            resource_name=name,
        )
        db.add(log)
        return {"success": True, "message": f"SQL file imported into database '{name}' successfully"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/adminer/status")
async def adminer_status(user: User = Depends(get_current_user)):
    """Check Adminer Web GUI status."""
    return await database_service.get_adminer_status()


@router.post("/adminer/install")
async def adminer_install(user: User = Depends(get_current_user)):
    """Install single-file Adminer for Web GUI database management."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    res = await database_service.install_adminer()
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Installation failed"))
    return res
