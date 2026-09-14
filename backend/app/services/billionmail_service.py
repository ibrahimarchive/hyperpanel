"""
BillionMail integration service.
One-click install/manage BillionMail mail server.
"""

import logging
from typing import Optional
from app.utils.command import run_sudo, run_command

logger = logging.getLogger(__name__)

PRIMARY_DIR = "/opt/BillionMail"
LEGACY_DIR = "/opt/Billion-Mail"
BILLIONMAIL_REPO = "https://github.com/aaPanel/BillionMail"


class BillionMailService:
    """Manages BillionMail installation, containers, credentials, and service state."""

    async def _get_active_dir(self) -> Optional[str]:
        """Return the installed directory if present."""
        for path in (PRIMARY_DIR, LEGACY_DIR):
            res = await run_command(f"test -d {path} && echo yes || echo no", shell=True)
            if res.success and res.output.strip() == "yes":
                return path
        return None

    async def get_status(self) -> dict:
        """Check BillionMail installation and running status."""
        active_dir = await self._get_active_dir()
        installed = active_dir is not None

        # Check if Docker is installed
        docker_res = await run_command("which docker")
        docker_installed = docker_res.success and bool(docker_res.output.strip())

        if not installed:
            return {
                "installed": False,
                "running": False,
                "docker_installed": docker_installed,
                "url": None,
                "port": 8080,
                "directory": PRIMARY_DIR,
            }

        # Check if Docker containers are running
        running = False
        container_names = []
        if docker_installed:
            ps_res = await run_sudo(
                "docker ps --filter 'name=billionmail' --format '{{.Names}}|{{.Status}}|{{.Ports}}' 2>/dev/null",
                shell=True,
            )
            if ps_res.success and ps_res.output.strip():
                running = True
                container_names = [line.strip() for line in ps_res.output.strip().split("\n") if line.strip()]

        # Determine server IP
        ip_res = await run_command("hostname -I 2>/dev/null | awk '{print $1}'", shell=True)
        server_ip = ip_res.output.strip() if (ip_res.success and ip_res.output.strip()) else "127.0.0.1"

        return {
            "installed": installed,
            "running": running,
            "docker_installed": docker_installed,
            "url": f"http://{server_ip}:8080",
            "port": 8080,
            "directory": active_dir or PRIMARY_DIR,
            "containers": container_names,
        }

    async def install(self) -> dict:
        """Install BillionMail (requires Docker)."""
        # 1. Verify Docker is available
        docker_result = await run_command("which docker")
        if not docker_result.success or not docker_result.output.strip():
            return {
                "success": False,
                "error": "Docker is required for BillionMail. Please install Docker first from the Docker page.",
            }

        target_dir = PRIMARY_DIR

        # 2. Clone repo if directory doesn't exist
        clone_cmd = f"git clone --depth 1 {BILLIONMAIL_REPO} {target_dir}"
        clone_result = await run_sudo(clone_cmd, timeout=180)
        if not clone_result.success and "already exists" not in clone_result.stderr:
            logger.warning(f"Git clone error, attempting fallback: {clone_result.stderr}")

        # 3. Run installation script
        install_cmd = f"cd {target_dir} && bash install.sh"
        install_result = await run_sudo(install_cmd, shell=True, timeout=600)
        if not install_result.success:
            return {"success": False, "error": f"Installer script failed: {install_result.stderr}"}

        # 4. Open mail ports in UFW if firewall is present
        mail_ports = ["25/tcp", "465/tcp", "587/tcp", "110/tcp", "995/tcp", "143/tcp", "993/tcp", "8080/tcp"]
        for p in mail_ports:
            await run_sudo(f"ufw allow {p} comment 'BillionMail' 2>/dev/null || true", shell=True)

        logger.info("BillionMail installed successfully")
        return {"success": True}

    async def start(self) -> dict:
        """Start BillionMail containers."""
        active_dir = await self._get_active_dir() or PRIMARY_DIR
        cmd = f"cd {active_dir} && (docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || (which bm >/dev/null && bm start))"
        result = await run_sudo(cmd, shell=True, timeout=120)
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def stop(self) -> dict:
        """Stop BillionMail containers."""
        active_dir = await self._get_active_dir() or PRIMARY_DIR
        cmd = f"cd {active_dir} && (docker compose down 2>/dev/null || docker-compose down 2>/dev/null || (which bm >/dev/null && bm stop))"
        result = await run_sudo(cmd, shell=True, timeout=60)
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def restart(self) -> dict:
        """Restart BillionMail containers."""
        active_dir = await self._get_active_dir() or PRIMARY_DIR
        cmd = f"cd {active_dir} && (docker compose restart 2>/dev/null || docker-compose restart 2>/dev/null || (which bm >/dev/null && bm restart))"
        result = await run_sudo(cmd, shell=True, timeout=120)
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def get_credentials(self) -> dict:
        """Retrieve default credentials from BillionMail CLI."""
        active_dir = await self._get_active_dir() or PRIMARY_DIR
        res = await run_sudo("which bm >/dev/null && bm default || (test -f /opt/BillionMail/bm && bash /opt/BillionMail/bm default)", shell=True)
        raw_output = res.output.strip() if res.success else ""
        return {"raw": raw_output}

    async def uninstall(self) -> dict:
        """Uninstall BillionMail and free resources."""
        await self.stop()
        active_dir = await self._get_active_dir() or PRIMARY_DIR
        res = await run_sudo(f"rm -rf {active_dir} /usr/bin/bm /usr/local/bin/bm 2>/dev/null || true", shell=True)
        return {"success": res.success}


# Singleton
billionmail_service = BillionMailService()
