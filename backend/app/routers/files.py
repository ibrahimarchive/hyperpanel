"""
File Manager API routes.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

from app.middleware.auth import get_current_user
from app.models.user import User, UserRole
from app.services.file_service import file_service
from app.config import settings

router = APIRouter(prefix="/api/files", tags=["File Manager"])


def _get_base_dir(user: User) -> str:
    """Get the base directory for a user's files."""
    if user.role == UserRole.ADMIN:
        return settings.WEBSITES_ROOT
    return user.home_directory or os.path.join(settings.WEBSITES_ROOT, user.username)


@router.get("/list")
async def list_directory(
    path: str = "",
    user: User = Depends(get_current_user),
):
    """List contents of a directory."""
    base_dir = _get_base_dir(user)
    result = file_service.list_directory(base_dir, path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/read")
async def read_file(
    path: str,
    user: User = Depends(get_current_user),
):
    """Read a file's contents for the editor."""
    base_dir = _get_base_dir(user)
    result = file_service.read_file(base_dir, path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/write")
async def write_file(
    path: str,
    content: str,
    user: User = Depends(get_current_user),
):
    """Write content to a file."""
    base_dir = _get_base_dir(user)
    result = file_service.write_file(base_dir, path, content)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/mkdir")
async def create_directory(
    path: str,
    user: User = Depends(get_current_user),
):
    """Create a new directory."""
    base_dir = _get_base_dir(user)
    result = file_service.create_directory(base_dir, path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/delete")
async def delete_item(
    path: str,
    user: User = Depends(get_current_user),
):
    """Delete a file or directory."""
    base_dir = _get_base_dir(user)
    result = file_service.delete_item(base_dir, path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/rename")
async def rename_item(
    path: str,
    new_name: str,
    user: User = Depends(get_current_user),
):
    """Rename a file or directory."""
    base_dir = _get_base_dir(user)
    result = file_service.rename_item(base_dir, path, new_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/upload")
async def upload_file(
    path: str = Form(""),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Upload a file."""
    base_dir = _get_base_dir(user)
    from app.utils.validators import sanitize_path
    
    target_dir = sanitize_path(path, base_dir) if path else base_dir
    if not target_dir:
        raise HTTPException(status_code=400, detail="Invalid upload path")

    target_path = os.path.join(target_dir, file.filename)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    return {"success": True, "filename": file.filename, "size": len(content)}


@router.get("/download")
async def download_file(
    path: str,
    user: User = Depends(get_current_user),
):
    """Download a file."""
    base_dir = _get_base_dir(user)
    from app.utils.validators import sanitize_path
    
    safe_path = sanitize_path(path, base_dir)
    if not safe_path or not os.path.isfile(safe_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        safe_path,
        filename=os.path.basename(safe_path),
    )


@router.post("/compress")
async def compress_files(
    paths: list[str],
    archive_name: str = "archive.tar.gz",
    user: User = Depends(get_current_user),
):
    """Compress files/directories into an archive."""
    base_dir = _get_base_dir(user)
    result = await file_service.compress(base_dir, paths, archive_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Compression failed"))
    return result


@router.post("/extract")
async def extract_archive(
    path: str,
    dest: str = "",
    user: User = Depends(get_current_user),
):
    """Extract an archive."""
    base_dir = _get_base_dir(user)
    result = await file_service.extract(base_dir, path, dest)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Extraction failed"))
    return result
