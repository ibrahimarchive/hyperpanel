"""
Docker management service.
Manages Docker installation, containers, and images.
"""

import logging
from typing import Optional

from app.utils.command import run_sudo, run_command

logger = logging.getLogger(__name__)


class DockerService:
    """Manages Docker Engine, containers, and images."""

    async def get_status(self) -> dict:
        """Check if Docker is installed and running."""
        # Check if docker binary exists
        which_result = await run_command("which docker")
        installed = which_result.success and which_result.output.strip() != ""

        if not installed:
            return {"installed": False, "running": False, "version": None}

        # Check version
        ver_result = await run_command("docker --version")
        version = ver_result.output.strip() if ver_result.success else None

        # Check if daemon is running
        info_result = await run_sudo("docker info --format '{{.ServerVersion}}'")
        running = info_result.success

        # Get counts
        containers_total = 0
        containers_running = 0
        images_count = 0

        if running:
            ct_result = await run_sudo("docker ps -a --format '{{.ID}}' | wc -l", shell=True)
            if ct_result.success:
                try:
                    containers_total = int(ct_result.output.strip())
                except ValueError:
                    pass

            cr_result = await run_sudo("docker ps --format '{{.ID}}' | wc -l", shell=True)
            if cr_result.success:
                try:
                    containers_running = int(cr_result.output.strip())
                except ValueError:
                    pass

            img_result = await run_sudo("docker images --format '{{.ID}}' | wc -l", shell=True)
            if img_result.success:
                try:
                    images_count = int(img_result.output.strip())
                except ValueError:
                    pass

        return {
            "installed": installed,
            "running": running,
            "version": version,
            "containers_total": containers_total,
            "containers_running": containers_running,
            "images_count": images_count,
        }

    async def install_docker(self) -> dict:
        """Install Docker Engine on Ubuntu/Debian."""
        # Use official get.docker.com convenience script with fallback
        install_cmd = (
            "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && "
            "sh /tmp/get-docker.sh && "
            "rm -f /tmp/get-docker.sh && "
            "systemctl enable --now docker && "
            "usermod -aG docker hyperpanel 2>/dev/null || true"
        )
        result = await run_sudo(install_cmd, shell=True, timeout=600)
        if not result.success:
            logger.error(f"Docker installation script failed: {result.stderr}")
            return {"success": False, "error": f"Installation script failed: {result.stderr}"}

        logger.info("Docker installed successfully")
        return {"success": True}

    async def uninstall_docker(self) -> dict:
        """Uninstall Docker Engine and free up resources."""
        cmd = (
            "systemctl stop docker 2>/dev/null || true; "
            "systemctl stop containerd 2>/dev/null || true; "
            "apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker.io 2>/dev/null || true; "
            "apt-get autoremove -y --purge 2>/dev/null || true; "
            "rm -rf /var/lib/docker /etc/docker"
        )
        result = await run_sudo(cmd, shell=True, timeout=300)
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def list_containers(self) -> list[dict]:
        """List all Docker containers."""
        result = await run_sudo(
            'docker ps -a --format \'{"id":"{{.ID}}","name":"{{.Names}}","image":"{{.Image}}","status":"{{.Status}}","state":"{{.State}}","ports":"{{.Ports}}","created":"{{.CreatedAt}}"}\'',
            shell=True,
        )
        if not result.success:
            return []

        import json
        containers = []
        for line in result.output.strip().split("\n"):
            line = line.strip()
            if line:
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return containers

    async def container_action(self, container_id: str, action: str) -> dict:
        """Perform an action on a container: start, stop, restart, remove."""
        if action not in ("start", "stop", "restart", "remove"):
            return {"success": False, "error": f"Invalid action: {action}"}

        cmd = f"docker {action}"
        if action == "remove":
            cmd = "docker rm -f"

        result = await run_sudo(f"{cmd} {container_id}")
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """Get logs from a container."""
        result = await run_sudo(f"docker logs --tail {tail} {container_id}")
        if result.success:
            return result.stdout + result.stderr
        return result.stderr or "Failed to get logs"

    async def create_container(
        self,
        image: str,
        name: Optional[str] = None,
        ports: Optional[str] = None,
        volumes: Optional[str] = None,
        env_vars: Optional[str] = None,
        restart_policy: str = "unless-stopped",
    ) -> dict:
        """Create and start a new container."""
        cmd = f"docker run -d --restart {restart_policy}"
        if name:
            cmd += f" --name {name}"
        if ports:
            for p in ports.split(","):
                p = p.strip()
                if p:
                    cmd += f" -p {p}"
        if volumes:
            for v in volumes.split(","):
                v = v.strip()
                if v:
                    cmd += f" -v {v}"
        if env_vars:
            for e in env_vars.split(","):
                e = e.strip()
                if e:
                    cmd += f" -e {e}"
        cmd += f" {image}"

        result = await run_sudo(cmd, shell=True)
        if result.success:
            container_id = result.output.strip()[:12]
            return {"success": True, "container_id": container_id}
        return {"success": False, "error": result.stderr}

    async def list_images(self) -> list[dict]:
        """List Docker images."""
        result = await run_sudo(
            'docker images --format \'{"id":"{{.ID}}","repository":"{{.Repository}}","tag":"{{.Tag}}","size":"{{.Size}}","created":"{{.CreatedAt}}"}\'',
            shell=True,
        )
        if not result.success:
            return []

        import json
        images = []
        for line in result.output.strip().split("\n"):
            line = line.strip()
            if line:
                try:
                    images.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return images

    async def pull_image(self, image: str) -> dict:
        """Pull a Docker image."""
        result = await run_sudo(f"docker pull {image}", timeout=300)
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def remove_image(self, image_id: str) -> dict:
        """Remove a Docker image."""
        result = await run_sudo(f"docker rmi -f {image_id}")
        return {"success": result.success, "error": result.stderr if not result.success else None}


# Singleton
docker_service = DockerService()
