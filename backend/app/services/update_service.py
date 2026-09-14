"""
HyperPanel update service.
Checks GitHub Releases API for official releases and applies updates safely.
"""

import logging
from pathlib import Path
from typing import Optional
import httpx

from app.config import settings
from app.utils.command import run_sudo, run_command

logger = logging.getLogger(__name__)

GITHUB_REPO = "ibrahimarchive/hyperpanel"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def parse_semver(v: str) -> tuple[int, ...]:
    """Parse a version string like 'v1.0.1' or '1.0.0' into an integer tuple for comparison."""
    clean = v.strip().lstrip("v").split("-")[0]
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


class UpdateService:
    """Manages official GitHub release checks and self-update orchestration."""

    def __init__(self):
        # Determine panel root directory (e.g. /opt/hyperpanel)
        self.panel_dir = Path(__file__).resolve().parent.parent.parent.parent

    async def check_update(self) -> dict:
        """Query GitHub Releases API and compare with local PANEL_VERSION."""
        current_ver = settings.PANEL_VERSION
        current_tuple = parse_semver(current_ver)

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(
                    RELEASES_API_URL,
                    headers={
                        "User-Agent": "HyperPanel-ControlPanel",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )

            if response.status_code == 200:
                data = response.json()
                tag_name = data.get("tag_name", "")
                remote_ver = tag_name.lstrip("v")
                remote_tuple = parse_semver(remote_ver)

                # Determine if an update is available:
                # 1. Semver is strictly greater
                # 2. Or tag is non-semver (e.g. "beta", "alpha") and differs from current version
                # 3. Or version strings are different
                has_update = False
                if tag_name:
                    if remote_tuple > current_tuple:
                        has_update = True
                    elif tag_name.lower() in ("beta", "alpha", "latest", "rc"):
                        has_update = True
                    elif remote_ver != current_ver and tag_name != f"v{current_ver}":
                        has_update = True

                return {
                    "has_update": has_update,
                    "update_available": has_update,
                    "current_version": current_ver,
                    "latest_version": remote_ver or current_ver,
                    "tag_name": tag_name,
                    "release_name": data.get("name") or tag_name,
                    "release_notes": data.get("body") or "Official update is ready for installation.",
                    "published_at": data.get("published_at"),
                    "html_url": data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases"),
                    "release_url": data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases"),
                }

            elif response.status_code == 404:
                # No published releases yet on the repository
                return {
                    "has_update": False,
                    "update_available": False,
                    "current_version": current_ver,
                    "latest_version": current_ver,
                    "tag_name": f"v{current_ver}",
                    "release_name": f"Version {current_ver}",
                    "release_notes": "You are on the latest release. No new official releases found on GitHub.",
                    "published_at": None,
                    "html_url": f"https://github.com/{GITHUB_REPO}",
                    "release_url": f"https://github.com/{GITHUB_REPO}",
                }
            else:
                logger.warning(f"GitHub Releases API returned status {response.status_code}")
                return {
                    "has_update": False,
                    "update_available": False,
                    "current_version": current_ver,
                    "latest_version": current_ver,
                    "tag_name": f"v{current_ver}",
                    "release_name": f"Version {current_ver}",
                    "release_notes": f"Unable to check for updates (GitHub API status {response.status_code}).",
                    "published_at": None,
                    "html_url": f"https://github.com/{GITHUB_REPO}",
                    "release_url": f"https://github.com/{GITHUB_REPO}",
                }

        except Exception as e:
            logger.error(f"Error checking GitHub Releases: {e}")
            return {
                "has_update": False,
                "update_available": False,
                "current_version": current_ver,
                "latest_version": current_ver,
                "tag_name": f"v{current_ver}",
                "release_name": f"Version {current_ver}",
                "release_notes": f"Could not connect to GitHub API: {str(e)}",
                "published_at": None,
                "html_url": f"https://github.com/{GITHUB_REPO}",
                "release_url": f"https://github.com/{GITHUB_REPO}",
            }

    async def apply_update(self, target_tag: Optional[str] = None) -> dict:
        """
        Trigger a detached background update script that checks out the specified release tag,
        updates dependencies, syncs Nginx, and restarts the systemd service without killing itself.
        """
        panel_path = str(self.panel_dir).replace("\\", "/")
        tag = target_tag.strip() if target_tag else ""

        checkout_cmd = f"git checkout tags/{tag}" if tag else "git pull origin main"

        script_content = f"""#!/bin/bash
exec > /tmp/hyperpanel_update.log 2>&1
echo "=== HyperPanel Update Started at $(date) ==="
echo "Target Tag: {tag or 'latest-main'}"

# Sleep 2 seconds to allow the HTTP response to be returned to the client
sleep 2

cd "{panel_path}" || cd /opt/hyperpanel || exit 1

echo "Fetching git tags..."
git fetch --tags --force origin
git fetch --force origin main

echo "Checking out {tag or 'latest'}..."
git checkout -B "{tag}" "tags/{tag}" 2>/dev/null || git checkout -B "{tag}" "{tag}" 2>/dev/null || git reset --hard origin/main

# Make sure scripts remain executable
chmod +x install.sh update.sh 2>/dev/null || true

# Update Python dependencies
if [ -f "backend/requirements.txt" ] && [ -d "backend/venv" ]; then
    echo "Updating dependencies..."
    ./backend/venv/bin/pip install -r backend/requirements.txt -q
fi

# Pre-initialize DB migrations and sync Nginx proxy
if [ -d "backend/venv" ]; then
    ./backend/venv/bin/python3 -c "import asyncio; from app.database import init_db; asyncio.run(init_db())" 2>/dev/null || true
    ./backend/venv/bin/python3 -c "import asyncio; from app.services.panel_settings_service import panel_settings_service; asyncio.run(panel_settings_service.sync_nginx_config())" 2>/dev/null || true
fi

echo "Reloading Nginx and restarting HyperPanel service..."
nginx -t && systemctl reload nginx 2>/dev/null || true
systemctl restart hyperpanel

echo "=== Update Completed Successfully ==="
"""

        # Write script to temporary location
        script_file = "/tmp/hyperpanel_update_runner.sh"
        write_cmd = f"cat << 'EOF' > {script_file}\n{script_content}\nEOF\nchmod +x {script_file}"
        await run_sudo(write_cmd, shell=True)

        # Launch detached via nohup
        launch_cmd = f"nohup bash {script_file} > /tmp/hyperpanel_update.log 2>&1 &"
        res = await run_sudo(launch_cmd, shell=True)

        logger.info(f"Update launched for tag '{tag}'")
        return {
            "status": "updating",
            "message": f"Update initiated to {tag or 'latest release'}. The panel will restart in ~5 seconds.",
            "target_tag": tag,
        }


# Singleton
update_service = UpdateService()
