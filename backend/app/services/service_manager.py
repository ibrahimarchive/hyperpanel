"""
Service manager — start/stop/restart/status for system services.
"""

import logging
from typing import Optional

from app.utils.command import run_sudo, run_command, check_service_status

logger = logging.getLogger(__name__)

# Services managed by HyperPanel, grouped by category
MANAGED_SERVICES = {
    "web": [
        {"name": "nginx", "label": "Nginx", "description": "Web Server"},
    ],
    "database": [
        {"name": "mysql", "label": "MySQL", "description": "Database Server"},
        {"name": "mariadb", "label": "MariaDB", "description": "Database Server"},
    ],
    "php": [
        {"name": "php7.4-fpm", "label": "PHP 7.4 FPM", "description": "PHP FastCGI"},
        {"name": "php8.0-fpm", "label": "PHP 8.0 FPM", "description": "PHP FastCGI"},
        {"name": "php8.1-fpm", "label": "PHP 8.1 FPM", "description": "PHP FastCGI"},
        {"name": "php8.2-fpm", "label": "PHP 8.2 FPM", "description": "PHP FastCGI"},
        {"name": "php8.3-fpm", "label": "PHP 8.3 FPM", "description": "PHP FastCGI"},
        {"name": "php8.4-fpm", "label": "PHP 8.4 FPM", "description": "PHP FastCGI"},
    ],
    "cache": [
        {"name": "redis-server", "label": "Redis", "description": "In-Memory Cache"},
        {"name": "memcached", "label": "Memcached", "description": "Memory Cache"},
    ],
    "security": [
        {"name": "ufw", "label": "UFW", "description": "Firewall"},
        {"name": "fail2ban", "label": "Fail2Ban", "description": "Intrusion Prevention"},
    ],
    "mail": [
        {"name": "postfix", "label": "Postfix", "description": "SMTP Server"},
        {"name": "dovecot", "label": "Dovecot", "description": "IMAP/POP3 Server"},
    ],
    "container": [
        {"name": "docker", "label": "Docker", "description": "Container Engine"},
    ],
    "ftp": [
        {"name": "pure-ftpd", "label": "Pure-FTPd", "description": "FTP Server"},
    ],
    "panel": [
        {"name": "hyperpanel", "label": "HyperPanel", "description": "Control Panel"},
    ],
}


class ServiceManagerService:
    """Manages systemd services."""

    async def list_services(self) -> list[dict]:
        """List all managed services with their status."""
        services = []

        for category, category_services in MANAGED_SERVICES.items():
            for svc in category_services:
                status = await self._get_service_info(svc["name"])
                if status.get("exists", False):
                    services.append({
                        "name": svc["name"],
                        "label": svc["label"],
                        "description": svc["description"],
                        "category": category,
                        **status,
                    })

        return services

    async def _get_service_info(self, service_name: str) -> dict:
        """Get detailed information about a service."""
        # Check if service exists
        exists_result = await run_command(f"systemctl list-unit-files {service_name}.service")
        exists = service_name in (exists_result.output if exists_result.success else "")

        if not exists:
            return {"exists": False}

        status = await check_service_status(service_name)

        # Get memory usage
        mem_result = await run_command(f"systemctl show {service_name} -p MemoryCurrent --value")
        memory_bytes = 0
        if mem_result.success and mem_result.output.strip() not in ("[not set]", "infinity", ""):
            try:
                memory_bytes = int(mem_result.output.strip())
            except ValueError:
                pass

        # Get uptime (ActiveEnterTimestamp)
        uptime_result = await run_command(f"systemctl show {service_name} -p ActiveEnterTimestamp --value")
        uptime_since = uptime_result.output.strip() if uptime_result.success else None

        # Get main PID
        pid_result = await run_command(f"systemctl show {service_name} -p MainPID --value")
        main_pid = 0
        if pid_result.success:
            try:
                main_pid = int(pid_result.output.strip())
            except ValueError:
                pass

        return {
            "exists": True,
            "active": status.get("active", False),
            "enabled": status.get("enabled", False),
            "status": status.get("status", "unknown"),
            "memory_bytes": memory_bytes,
            "uptime_since": uptime_since if uptime_since and uptime_since != "" else None,
            "main_pid": main_pid,
        }

    async def start_service(self, service_name: str) -> dict:
        """Start a systemd service."""
        self._validate_service(service_name)
        result = await run_sudo(f"systemctl start {service_name}")
        logger.info(f"Started service: {service_name} — success: {result.success}")
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def stop_service(self, service_name: str) -> dict:
        """Stop a systemd service."""
        self._validate_service(service_name)
        result = await run_sudo(f"systemctl stop {service_name}")
        logger.info(f"Stopped service: {service_name} — success: {result.success}")
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def restart_service(self, service_name: str) -> dict:
        """Restart a systemd service."""
        self._validate_service(service_name)
        result = await run_sudo(f"systemctl restart {service_name}")
        logger.info(f"Restarted service: {service_name} — success: {result.success}")
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def enable_service(self, service_name: str) -> dict:
        """Enable a service to start on boot."""
        self._validate_service(service_name)
        result = await run_sudo(f"systemctl enable {service_name}")
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def disable_service(self, service_name: str) -> dict:
        """Disable a service from starting on boot."""
        self._validate_service(service_name)
        result = await run_sudo(f"systemctl disable {service_name}")
        return {"success": result.success, "error": result.stderr if not result.success else None}

    def _validate_service(self, service_name: str):
        """Ensure we only manage known services."""
        all_names = []
        for services in MANAGED_SERVICES.values():
            all_names.extend(s["name"] for s in services)

        if service_name not in all_names:
            raise ValueError(f"Service '{service_name}' is not managed by HyperPanel")


# Singleton
service_manager = ServiceManagerService()
