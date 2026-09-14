"""
Updates API routes.
Allows checking and applying official GitHub Releases directly from the panel.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.middleware.auth import require_admin, get_current_user
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.services.update_service import update_service
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/updates", tags=["Updates"])


class UpdateApplyRequest(BaseModel):
    target_tag: Optional[str] = None
    version: Optional[str] = None


@router.get("/check")
async def check_for_updates(user: User = Depends(get_current_user)):
    """Check GitHub Releases for official newer versions."""
    return await update_service.check_update()


@router.post("/apply")
@router.post("/trigger")
async def apply_update(
    data: Optional[UpdateApplyRequest] = None,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger one-click self-update to the official release."""
    target_tag = None
    if data:
        target_tag = data.target_tag or data.version
    result = await update_service.apply_update(target_tag=target_tag)

    db.add(ActivityLog(
        user_id=user.id,
        action="system.update",
        category="system",
        description=f"Triggered panel self-update to '{target_tag or 'latest'}'",
        resource_type="system",
        resource_name="hyperpanel",
    ))
    return result
