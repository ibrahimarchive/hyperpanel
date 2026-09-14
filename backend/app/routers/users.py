"""
User management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, ChangePasswordRequest
from app.services.user_service import user_service
from app.services.auth_service import verify_password

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("")
async def list_users(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """List all users (admin only)."""
    users = await user_service.get_users(db, skip, limit)
    return [
        {
            "id": u.id, "username": u.username, "email": u.email,
            "role": u.role.value if hasattr(u.role, 'value') else u.role,
            "is_active": u.is_active, "full_name": u.full_name,
            "max_websites": u.max_websites, "max_databases": u.max_databases,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin only)."""
    existing = await user_service.get_user_by_username(db, data.username)
    if existing:
        raise HTTPException(status_code=409, detail=f"Username '{data.username}' already exists")

    new_user = await user_service.create_user(
        db, data.username, data.email, data.password, data.role, data.full_name,
        max_websites=data.max_websites, max_databases=data.max_databases,
        max_domains=data.max_domains, disk_quota_mb=data.disk_quota_mb,
        bandwidth_quota_mb=data.bandwidth_quota_mb,
    )
    return {"id": new_user.id, "username": new_user.username, "message": "User created"}


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a user (admin only)."""
    updated = await user_service.update_user(
        db, user_id, **data.model_dump(exclude_none=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user (admin only)."""
    if user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    success = await user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    await user_service.change_password(db, user.id, data.new_password)
    return {"message": "Password changed successfully"}
