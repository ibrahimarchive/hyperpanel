"""
Log viewer API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from typing import Optional
import asyncio

from app.middleware.auth import require_admin
from app.models.user import User
from app.services.log_service import log_service
from app.utils.command import run_sudo

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("")
async def list_logs(user: User = Depends(require_admin)):
    """List all available log sources."""
    return log_service.get_available_logs()


@router.get("/sites/{domain}")
async def list_site_logs(
    domain: str,
    user: User = Depends(require_admin),
):
    """List available logs for a specific domain."""
    return await log_service.get_site_logs(domain)


@router.get("/{log_id}")
async def read_log(
    log_id: str,
    lines: int = Query(100, ge=10, le=5000),
    search: Optional[str] = None,
    site_domain: Optional[str] = None,
    user: User = Depends(require_admin),
):
    """Read the last N lines of a log file."""
    result = await log_service.read_log(
        log_id=log_id,
        lines=lines,
        search=search,
        site_domain=site_domain,
    )

    if "error" in result and result["error"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/{log_id}/download")
async def download_log(
    log_id: str,
    user: User = Depends(require_admin),
):
    """Download a log file."""
    filepath = await log_service.get_log_file_path(log_id)
    if not filepath:
        raise HTTPException(status_code=404, detail="Log file not found")

    return FileResponse(
        path=filepath,
        filename=filepath.split("/")[-1],
        media_type="text/plain",
    )
