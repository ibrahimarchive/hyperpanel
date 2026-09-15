"""
Log viewer service.
Reads and streams system log files.
"""

import logging
import shlex
import os
from pathlib import Path
from typing import Optional

from app.utils.command import run_sudo, run_command

logger = logging.getLogger(__name__)

# Predefined log files the panel can view
LOG_SOURCES = [
    {
        "id": "nginx_access",
        "label": "Nginx Access",
        "path": "/var/log/nginx/access.log",
        "category": "web",
    },
    {
        "id": "nginx_error",
        "label": "Nginx Error",
        "path": "/var/log/nginx/error.log",
        "category": "web",
    },
    {
        "id": "mysql_error",
        "label": "MySQL Error",
        "path": "/var/log/mysql/error.log",
        "category": "database",
    },
    {
        "id": "mysql_slow",
        "label": "MySQL Slow Query",
        "path": "/var/log/mysql/mysql-slow.log",
        "category": "database",
    },
    {
        "id": "syslog",
        "label": "System Log",
        "path": "/var/log/syslog",
        "category": "system",
    },
    {
        "id": "auth",
        "label": "Auth Log",
        "path": "/var/log/auth.log",
        "category": "security",
    },
    {
        "id": "fail2ban",
        "label": "Fail2Ban",
        "path": "/var/log/fail2ban.log",
        "category": "security",
    },
    {
        "id": "ufw",
        "label": "UFW Firewall",
        "path": "/var/log/ufw.log",
        "category": "security",
    },
    {
        "id": "php_fpm",
        "label": "PHP-FPM",
        "path": "/var/log/php*-fpm.log",
        "category": "php",
    },
    {
        "id": "hyperpanel",
        "label": "HyperPanel",
        "path": "/var/log/hyperpanel.log",
        "category": "panel",
    },
]


class LogService:
    """Reads and manages log files."""

    def get_available_logs(self) -> list[dict]:
        """Return a list of available (existing) log sources."""
        available = []
        for source in LOG_SOURCES:
            # For glob patterns (php*), always include
            if "*" in source["path"]:
                available.append({**source, "exists": True})
            else:
                available.append({
                    **source,
                    "exists": os.path.exists(source["path"]),
                })
        return available

    def _resolve_log_id(self, log_id: str) -> Optional[dict]:
        """Resolve a log_id to its source definition."""
        for source in LOG_SOURCES:
            if source["id"] == log_id:
                return source
        return None

    async def get_site_logs(self, domain: str) -> list[dict]:
        """Get available logs for a specific site/domain."""
        logs = []
        access_log = f"/var/log/nginx/{domain}-access.log"
        error_log = f"/var/log/nginx/{domain}-error.log"

        if os.path.exists(access_log):
            logs.append({
                "id": f"site_{domain}_access",
                "label": f"{domain} Access",
                "path": access_log,
                "category": "site",
            })
        if os.path.exists(error_log):
            logs.append({
                "id": f"site_{domain}_error",
                "label": f"{domain} Error",
                "path": error_log,
                "category": "site",
            })
        return logs

    async def read_log(
        self,
        log_id: str,
        lines: int = 100,
        search: Optional[str] = None,
        site_domain: Optional[str] = None,
    ) -> dict:
        """Read the last N lines of a log file."""
        # Resolve path
        if site_domain and log_id.startswith("site_"):
            if "access" in log_id:
                log_path = f"/var/log/nginx/{site_domain}-access.log"
            elif "error" in log_id:
                log_path = f"/var/log/nginx/{site_domain}-error.log"
            else:
                return {"lines": [], "error": "Invalid site log ID"}
        else:
            source = self._resolve_log_id(log_id)
            if not source:
                return {"lines": [], "error": f"Unknown log source: {log_id}"}
            log_path = source["path"]

        # Handle glob patterns
        if "*" in log_path:
            resolve_result = await run_command(f"ls {log_path} 2>/dev/null | head -1", shell=True)
            if resolve_result.success and resolve_result.output.strip():
                log_path = resolve_result.output.strip()
            else:
                return {"lines": [], "total_lines": 0, "file_size": 0}

        # Read with tail
        q_path = shlex.quote(log_path)
        safe_lines = int(lines) if isinstance(lines, int) or str(lines).isdigit() else 100

        if search:
            q_search = shlex.quote(search)
            cmd = f"grep -i {q_search} {q_path} | tail -n {safe_lines}"
        else:
            cmd = f"tail -n {safe_lines} {q_path}"

        result = await run_sudo(cmd, shell=True)
        if not result.success:
            return {"lines": [], "error": result.stderr}

        log_lines = result.output.split("\n") if result.output.strip() else []

        # Get file size
        size_result = await run_command(f"stat -c %s {log_path} 2>/dev/null || echo 0", shell=True)
        file_size = 0
        try:
            file_size = int(size_result.output.strip())
        except ValueError:
            pass

        # Get total line count
        count_result = await run_command(f"wc -l < {log_path} 2>/dev/null || echo 0", shell=True)
        total_lines = 0
        try:
            total_lines = int(count_result.output.strip())
        except ValueError:
            pass

        return {
            "lines": log_lines,
            "total_lines": total_lines,
            "file_size": file_size,
            "path": log_path,
        }

    async def get_log_file_path(self, log_id: str) -> Optional[str]:
        """Get the filesystem path for a log ID."""
        source = self._resolve_log_id(log_id)
        if not source:
            return None

        log_path = source["path"]
        if "*" in log_path:
            resolve_result = await run_command(f"ls {log_path} 2>/dev/null | head -1", shell=True)
            if resolve_result.success and resolve_result.output.strip():
                return resolve_result.output.strip()
            return None

        return log_path if os.path.exists(log_path) else None


# Singleton
log_service = LogService()
