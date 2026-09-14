"""
Fail2Ban management service.
"""

import logging
import re
from typing import Optional

from app.utils.command import run_sudo, run_command

logger = logging.getLogger(__name__)


class Fail2BanService:
    """Manages Fail2Ban installation, jails, and banned IPs."""

    async def get_status(self) -> dict:
        """Check if Fail2Ban is installed and running."""
        which_result = await run_command("which fail2ban-client")
        installed = which_result.success and which_result.output.strip() != ""

        if not installed:
            return {"installed": False, "running": False, "version": None, "jails": 0}

        ver_result = await run_command("fail2ban-client --version")
        version = ver_result.output.strip().split("\n")[0] if ver_result.success else None

        status_result = await run_sudo("fail2ban-client status")
        running = status_result.success

        jail_count = 0
        if running and status_result.output:
            match = re.search(r"Number of jail:\s*(\d+)", status_result.output)
            if match:
                jail_count = int(match.group(1))

        return {
            "installed": installed,
            "running": running,
            "version": version,
            "jails": jail_count,
        }

    async def install(self) -> dict:
        """Install Fail2Ban."""
        result = await run_sudo("apt-get update && apt-get install -y fail2ban", shell=True, timeout=120)
        if not result.success:
            return {"success": False, "error": result.stderr}

        # Enable and start
        await run_sudo("systemctl enable fail2ban")
        await run_sudo("systemctl start fail2ban")

        logger.info("Fail2Ban installed and started")
        return {"success": True}

    async def list_jails(self) -> list[dict]:
        """List all Fail2Ban jails with their status."""
        result = await run_sudo("fail2ban-client status")
        if not result.success:
            return []

        # Parse jail list
        jail_names = []
        match = re.search(r"Jail list:\s*(.*)", result.output)
        if match:
            jail_names = [j.strip() for j in match.group(1).split(",") if j.strip()]

        jails = []
        for name in jail_names:
            jail_info = await self.get_jail_status(name)
            if jail_info:
                jails.append(jail_info)

        return jails

    async def get_jail_status(self, jail_name: str) -> Optional[dict]:
        """Get detailed status of a specific jail."""
        result = await run_sudo(f"fail2ban-client status {jail_name}")
        if not result.success:
            return None

        output = result.output

        currently_failed = 0
        total_failed = 0
        currently_banned = 0
        total_banned = 0
        banned_ips = []

        match = re.search(r"Currently failed:\s*(\d+)", output)
        if match:
            currently_failed = int(match.group(1))

        match = re.search(r"Total failed:\s*(\d+)", output)
        if match:
            total_failed = int(match.group(1))

        match = re.search(r"Currently banned:\s*(\d+)", output)
        if match:
            currently_banned = int(match.group(1))

        match = re.search(r"Total banned:\s*(\d+)", output)
        if match:
            total_banned = int(match.group(1))

        match = re.search(r"Banned IP list:\s*(.*)", output)
        if match and match.group(1).strip():
            banned_ips = [ip.strip() for ip in match.group(1).split() if ip.strip()]

        return {
            "name": jail_name,
            "currently_failed": currently_failed,
            "total_failed": total_failed,
            "currently_banned": currently_banned,
            "total_banned": total_banned,
            "banned_ips": banned_ips,
        }

    async def ban_ip(self, jail_name: str, ip: str) -> dict:
        """Manually ban an IP in a jail."""
        result = await run_sudo(f"fail2ban-client set {jail_name} banip {ip}")
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def unban_ip(self, jail_name: str, ip: str) -> dict:
        """Unban an IP from a jail."""
        result = await run_sudo(f"fail2ban-client set {jail_name} unbanip {ip}")
        return {"success": result.success, "error": result.stderr if not result.success else None}


# Singleton
fail2ban_service = Fail2BanService()
