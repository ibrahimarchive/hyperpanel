"""
File management service.
Provides directory listing, file CRUD, upload/download, and archive operations.
"""

import os
import stat
import logging
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.config import settings
from app.utils.command import run_command, run_sudo
from app.utils.validators import sanitize_path

logger = logging.getLogger(__name__)


class FileService:
    """Manages file system operations within user-scoped directories."""

    def list_directory(self, base_dir: str, relative_path: str = "") -> dict:
        """List contents of a directory."""
        safe_path = sanitize_path(relative_path, base_dir) if relative_path else base_dir
        if not safe_path:
            return {"success": False, "error": "Invalid path"}

        try:
            path = Path(safe_path)
            if not path.exists() or not path.is_dir():
                return {"success": False, "error": "Directory not found"}

            items = []
            for entry in sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                try:
                    entry_stat = entry.stat()
                    items.append({
                        "name": entry.name,
                        "path": str(entry.relative_to(base_dir)),
                        "type": "directory" if entry.is_dir() else "file",
                        "size": entry_stat.st_size if entry.is_file() else 0,
                        "modified": datetime.fromtimestamp(entry_stat.st_mtime).isoformat(),
                        "permissions": stat.filemode(entry_stat.st_mode),
                        "owner": str(entry_stat.st_uid),
                    })
                except (PermissionError, OSError):
                    continue

            return {
                "success": True,
                "path": str(path.relative_to(base_dir)) if str(path) != base_dir else "/",
                "items": items,
                "parent": str(path.parent.relative_to(base_dir)) if str(path) != base_dir else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_file(self, base_dir: str, relative_path: str) -> dict:
        """Read a file's contents (for the code editor)."""
        safe_path = sanitize_path(relative_path, base_dir)
        if not safe_path:
            return {"success": False, "error": "Invalid path"}

        try:
            path = Path(safe_path)
            if not path.exists() or not path.is_file():
                return {"success": False, "error": "File not found"}

            # Check if file is too large (> 5MB) or binary
            size = path.stat().st_size
            if size > 5 * 1024 * 1024:
                return {"success": False, "error": "File too large for editor (max 5MB)"}

            mime = mimetypes.guess_type(str(path))[0]
            if mime and not mime.startswith("text/") and mime not in (
                "application/json", "application/xml", "application/javascript",
                "application/x-yaml", "application/x-sh",
            ):
                return {"success": False, "error": "Binary file cannot be edited", "mime": mime}

            content = path.read_text(encoding="utf-8", errors="replace")
            return {
                "success": True,
                "content": content,
                "name": path.name,
                "size": size,
                "mime": mime or "text/plain",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, base_dir: str, relative_path: str, content: str) -> dict:
        """Write content to a file."""
        safe_path = sanitize_path(relative_path, base_dir)
        if not safe_path:
            return {"success": False, "error": "Invalid path"}

        try:
            path = Path(safe_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(path.relative_to(base_dir))}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_directory(self, base_dir: str, relative_path: str) -> dict:
        """Create a new directory."""
        safe_path = sanitize_path(relative_path, base_dir)
        if not safe_path:
            return {"success": False, "error": "Invalid path"}

        try:
            path = Path(safe_path)
            path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(path.relative_to(base_dir))}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_item(self, base_dir: str, relative_path: str) -> dict:
        """Delete a file or directory."""
        safe_path = sanitize_path(relative_path, base_dir)
        if not safe_path:
            return {"success": False, "error": "Invalid path"}

        try:
            path = Path(safe_path)
            if not path.exists():
                return {"success": False, "error": "Item not found"}

            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rename_item(self, base_dir: str, old_path: str, new_name: str) -> dict:
        """Rename a file or directory."""
        safe_path = sanitize_path(old_path, base_dir)
        if not safe_path:
            return {"success": False, "error": "Invalid path"}

        try:
            source = Path(safe_path)
            if not source.exists():
                return {"success": False, "error": "Item not found"}

            target = source.parent / new_name
            source.rename(target)
            return {"success": True, "new_path": str(target.relative_to(base_dir))}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def compress(self, base_dir: str, paths: list, archive_name: str) -> dict:
        """Compress files/directories into a tar.gz archive."""
        safe_paths = []
        for p in paths:
            sp = sanitize_path(p, base_dir)
            if sp:
                safe_paths.append(sp)

        if not safe_paths:
            return {"success": False, "error": "No valid paths to compress"}

        output = Path(base_dir) / archive_name
        items = " ".join(f"'{p}'" for p in safe_paths)
        result = await run_command(f"tar -czf '{output}' -C '{base_dir}' {items}", shell=True)
        return {"success": result.success, "archive": str(output), "error": result.stderr if not result.success else None}

    async def extract(self, base_dir: str, archive_path: str, dest: str = "") -> dict:
        """Extract an archive."""
        safe_archive = sanitize_path(archive_path, base_dir)
        if not safe_archive:
            return {"success": False, "error": "Invalid archive path"}

        dest_path = Path(base_dir) / dest if dest else Path(base_dir)
        result = await run_command(f"tar -xzf '{safe_archive}' -C '{dest_path}'")
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def change_permissions(self, base_dir: str, relative_path: str, mode: str) -> dict:
        """Change file permissions (chmod)."""
        safe_path = sanitize_path(relative_path, base_dir)
        if not safe_path:
            return {"success": False, "error": "Invalid path"}

        result = await run_sudo(f"chmod {mode} '{safe_path}'")
        return {"success": result.success}


# Singleton
file_service = FileService()
