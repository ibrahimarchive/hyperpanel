"""
PHP version management service.
Install, configure, and manage PHP-FPM versions.
"""

import logging
import re
from typing import Optional

from app.utils.command import run_sudo, run_command

logger = logging.getLogger(__name__)

AVAILABLE_PHP_VERSIONS = ["7.4", "8.0", "8.1", "8.2", "8.3", "8.4"]

COMMON_EXTENSIONS = [
    "cli", "fpm", "common", "mysql", "pgsql", "sqlite3", "curl", "gd",
    "mbstring", "xml", "zip", "bcmath", "intl", "soap", "redis",
    "imagick", "memcached", "opcache", "readline",
]

COMMON_INI_DIRECTIVES = [
    "upload_max_filesize", "post_max_size", "memory_limit",
    "max_execution_time", "max_input_time", "max_input_vars",
    "display_errors", "error_reporting", "date.timezone",
    "session.gc_maxlifetime", "opcache.enable",
]


class PHPService:
    """Manages PHP versions and configurations."""

    async def list_installed_versions(self) -> list[dict]:
        """List all installed PHP versions with status."""
        result = await run_command("ls /etc/php/ 2>/dev/null", shell=True)
        if not result.success or not result.output.strip():
            return []

        versions = []
        for ver in result.output.strip().split():
            ver = ver.strip()
            if re.match(r"^\d+\.\d+$", ver):
                info = await self._get_version_info(ver)
                versions.append(info)

        return sorted(versions, key=lambda v: v["version"])

    async def _get_version_info(self, version: str) -> dict:
        """Get info for a specific PHP version."""
        # Check FPM status
        fpm_name = f"php{version}-fpm"
        active_result = await run_command(f"systemctl is-active {fpm_name}")
        is_active = active_result.success and active_result.output.strip() == "active"

        enabled_result = await run_command(f"systemctl is-enabled {fpm_name}")
        is_enabled = enabled_result.success and enabled_result.output.strip() == "enabled"

        # Count extensions
        ext_result = await run_command(f"php{version} -m 2>/dev/null | wc -l", shell=True)
        ext_count = 0
        if ext_result.success:
            try:
                ext_count = int(ext_result.output.strip())
            except ValueError:
                pass

        return {
            "version": version,
            "fpm_service": fpm_name,
            "active": is_active,
            "enabled": is_enabled,
            "extensions_count": ext_count,
        }

    async def install_version(self, version: str) -> dict:
        """Install a PHP version with common extensions."""
        if version not in AVAILABLE_PHP_VERSIONS:
            return {"success": False, "error": f"Invalid PHP version: {version}"}

        # Add ondrej PPA if not present
        await run_sudo("add-apt-repository -y ppa:ondrej/php 2>/dev/null || true", shell=True, timeout=60)
        await run_sudo("apt-get update", timeout=60)

        # Install PHP + common extensions
        packages = [f"php{version}-{ext}" for ext in COMMON_EXTENSIONS]
        pkg_str = " ".join(packages)

        result = await run_sudo(f"apt-get install -y {pkg_str}", timeout=300)
        if not result.success:
            return {"success": False, "error": result.stderr}

        # Enable and start FPM
        await run_sudo(f"systemctl enable php{version}-fpm")
        await run_sudo(f"systemctl start php{version}-fpm")

        logger.info(f"PHP {version} installed successfully")
        return {"success": True}

    async def remove_version(self, version: str) -> dict:
        """Remove a PHP version."""
        result = await run_sudo(f"apt-get purge -y 'php{version}-*'", shell=True, timeout=120)
        await run_sudo("apt-get autoremove -y", timeout=60)
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def list_extensions(self, version: str) -> list[dict]:
        """List extensions for a PHP version with enabled status."""
        result = await run_command(f"php{version} -m 2>/dev/null", shell=True)
        enabled = set()
        if result.success:
            enabled = {ext.strip().lower() for ext in result.output.strip().split("\n") if ext.strip()}

        # List available extensions
        avail_result = await run_command(
            f"apt-cache search '^php{version}-' | awk '{{print $1}}' | sed 's/php{version}-//'",
            shell=True,
        )
        available = []
        if avail_result.success:
            for ext in avail_result.output.strip().split("\n"):
                ext = ext.strip()
                if ext:
                    available.append({
                        "name": ext,
                        "enabled": ext.lower() in enabled,
                        "package": f"php{version}-{ext}",
                    })

        return sorted(available, key=lambda e: e["name"])

    async def toggle_extension(self, version: str, extension: str, enable: bool) -> dict:
        """Enable or disable a PHP extension."""
        if enable:
            # Install if not present, then enable
            await run_sudo(f"apt-get install -y php{version}-{extension}", timeout=60)
            result = await run_sudo(f"phpenmod -v {version} {extension}")
        else:
            result = await run_sudo(f"phpdismod -v {version} {extension}")

        # Restart FPM
        await run_sudo(f"systemctl restart php{version}-fpm")
        return {"success": result.success}

    async def get_config(self, version: str) -> dict:
        """Get common php.ini settings."""
        ini_path = f"/etc/php/{version}/fpm/php.ini"
        config = {}

        for directive in COMMON_INI_DIRECTIVES:
            result = await run_command(
                f"php{version} -c {ini_path} -r \"echo ini_get('{directive}');\" 2>/dev/null",
                shell=True,
            )
            config[directive] = result.output.strip() if result.success else ""

        return {"version": version, "ini_path": ini_path, "directives": config}

    async def update_config(self, version: str, directives: dict) -> dict:
        """Update php.ini settings."""
        ini_path = f"/etc/php/{version}/fpm/php.ini"

        for key, value in directives.items():
            if key not in COMMON_INI_DIRECTIVES:
                continue
            # Use sed to update the directive
            await run_sudo(
                f"sed -i 's/^;*\\s*{key}\\s*=.*/{key} = {value}/' {ini_path}",
                shell=True,
            )

        # Restart FPM
        result = await run_sudo(f"systemctl restart php{version}-fpm")
        return {"success": result.success}

    async def restart_fpm(self, version: str) -> dict:
        """Restart PHP-FPM for a version."""
        result = await run_sudo(f"systemctl restart php{version}-fpm")
        return {"success": result.success}


# Singleton
php_service = PHPService()
