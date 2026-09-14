"""
Process management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.services.process_service import process_service

router = APIRouter(prefix="/api/processes", tags=["Processes"])


@router.get("")
async def list_processes(
    sort: str = Query("cpu", regex="^(cpu|memory)$"),
    limit: int = Query(50, ge=10, le=200),
    search: Optional[str] = None,
    user: User = Depends(require_admin),
):
    """List running processes sorted by CPU or memory usage."""
    return process_service.get_process_list(sort_by=sort, limit=limit, search=search)


@router.get("/summary")
async def process_summary(user: User = Depends(require_admin)):
    """Get process count summary and load averages."""
    return process_service.get_summary()


@router.post("/{pid}/kill")
async def kill_process(
    pid: int,
    user: User = Depends(require_admin),
):
    """Kill a process by PID. Admin only."""
    result = process_service.kill_process(pid)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to kill process"))
    return {"message": f"Process {pid} ({result.get('process', '')}) terminated"}
