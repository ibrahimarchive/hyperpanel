"""
Nginx service.
Manages virtual host configurations, PHP-FPM pools, and Nginx operations.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from app.config import settings
from app.utils.command import run_command, run_sudo
from app.utils.template import render_template

logger = logging.getLogger(__name__)


class NginxService:
    """Manages Nginx virtual hosts and related configurations."""

    def __init__(self):
        self.sites_available = Path(settings.NGINX_SITES_DIR)
        self.sites_enabled = Path(settings.NGINX_SITES_ENABLED)
        self.www_root = Path(settings.WEBSITES_ROOT)

    async def create_website(
        self,
        domain: str,
        site_type: str = "php",
        php_version: str = "8.2",
        proxy_port: Optional[int] = None,
        proxy_address: str = "127.0.0.1",
        user: str = "www-data",
    ) -> dict:
        """
        Create a new website with Nginx config and document root.
        
        Returns dict with status and document_root path.
        """
        doc_root = self.www_root / domain / "public_html"
        log_dir = self.www_root / domain / "logs"

        # Create directories
        await run_sudo(f"mkdir -p {doc_root}")
        await run_sudo(f"mkdir -p {log_dir}")
        await run_sudo(f"chown -R {user}:{user} {self.www_root / domain}")
        await run_sudo(f"chmod -R 755 {self.www_root / domain}")

        # Create default index file
        if site_type == "php":
            index_content = f"""<?php
// Welcome to {domain}
// Managed by HyperPanel
phpinfo();
"""
            index_file = doc_root / "index.php"
        else:
            index_content = f"""<!DOCTYPE html>
<html>
<head><title>Welcome to {domain}</title></head>
<body>
<h1>Welcome to {domain}</h1>
<p>This site is managed by HyperPanel.</p>
</body>
</html>
"""
            index_file = doc_root / "index.html"

        # Write index file safely without bash history expansion (!) issues
        cat_cmd = f"bash -c 'cat > {index_file} << \"HTMLEOF\"\n{index_content}\nHTMLEOF'"
        await run_sudo(cat_cmd, shell=True)
        await run_sudo(f"chown {user}:{user} {index_file}")
        await run_sudo(f"chmod 644 {index_file}")

        # Verify active PHP socket if php site
        if site_type == "php":
            sock_check = await run_command(f"test -S /run/php/php{php_version}-fpm.sock")
            if not sock_check.success:
                # Find available PHP sock
                find_sock = await run_command("ls /run/php/php*-fpm.sock 2>/dev/null", shell=True)
                if find_sock.success and find_sock.output.strip():
                    import re
                    m = re.search(r"php([0-9.]+)-fpm\.sock", find_sock.output.strip().split()[0])
                    if m:
                        php_version = m.group(1)

        # Check for panel SSL fallback
        panel_cert = Path("/opt/hyperpanel/ssl/panel.crt")
        has_fallback_ssl = panel_cert.exists() and panel_cert.stat().st_size > 0

        # Generate Nginx config from template
        template_name = "nginx_vhost.conf.j2"
        config = render_template(
            template_name,
            domain=domain,
            document_root=str(doc_root),
            access_log=str(log_dir / "access.log"),
            error_log=str(log_dir / "error.log"),
            site_type=site_type,
            php_version=php_version,
            proxy_port=proxy_port,
            proxy_address=proxy_address,
            has_fallback_ssl=has_fallback_ssl,
        )

        # Write config
        config_path = self.sites_available / f"{domain}.conf"
        await run_sudo(f"bash -c 'cat > {config_path} << \"NGXEOF\"\n{config}\nNGXEOF'", shell=True)

        # Enable site
        await self.enable_site(domain)

        # Test and reload
        test_result = await self.test_config()
        if test_result["success"]:
            await self.reload()
            return {
                "success": True,
                "document_root": str(doc_root),
                "config_path": str(config_path),
                "access_log": str(log_dir / "access.log"),
                "error_log": str(log_dir / "error.log"),
            }
        else:
            # Rollback: remove the config
            await run_sudo(f"rm -f {config_path}")
            await run_sudo(f"rm -f {self.sites_enabled / f'{domain}.conf'}")
            return {
                "success": False,
                "error": test_result["error"],
            }

    async def delete_website(self, domain: str, remove_files: bool = False) -> dict:
        """Delete a website's Nginx configuration and optionally its files."""
        config_path = self.sites_available / f"{domain}.conf"
        enabled_path = self.sites_enabled / f"{domain}.conf"

        # Disable and remove config
        await run_sudo(f"rm -f {enabled_path}")
        await run_sudo(f"rm -f {config_path}")

        # Optionally remove document root
        if remove_files:
            site_dir = self.www_root / domain
            await run_sudo(f"rm -rf {site_dir}")

        await self.reload()
        return {"success": True}

    async def enable_site(self, domain: str) -> dict:
        """Enable a site by creating a symlink in sites-enabled."""
        source = self.sites_available / f"{domain}.conf"
        target = self.sites_enabled / f"{domain}.conf"
        result = await run_sudo(f"ln -sf {source} {target}")
        return {"success": result.success}

    async def disable_site(self, domain: str) -> dict:
        """Disable a site by removing its symlink."""
        target = self.sites_enabled / f"{domain}.conf"
        result = await run_sudo(f"rm -f {target}")
        await self.reload()
        return {"success": result.success}

    async def test_config(self) -> dict:
        """Test Nginx configuration syntax."""
        result = await run_sudo("nginx -t")
        return {
            "success": result.success,
            "output": result.stderr if result.stderr else result.stdout,
            "error": result.stderr if not result.success else None,
        }

    async def reload(self) -> dict:
        """Gracefully reload Nginx."""
        result = await run_sudo("systemctl reload nginx")
        return {"success": result.success}

    async def restart(self) -> dict:
        """Restart Nginx."""
        result = await run_sudo("systemctl restart nginx")
        return {"success": result.success}

    async def get_status(self) -> dict:
        """Get Nginx service status."""
        result = await run_command("systemctl is-active nginx")
        return {
            "active": result.output == "active",
            "status": result.output,
        }

    async def update_ssl_config(
        self,
        domain: str,
        cert_path: str,
        key_path: str,
        chain_path: Optional[str] = None,
        force_https: bool = True,
        site_type: str = "php",
        php_version: str = "8.2",
        proxy_port: Optional[int] = None,
        proxy_address: str = "127.0.0.1",
    ) -> dict:
        """Update a site's Nginx config to include SSL."""
        config = render_template(
            "nginx_ssl_vhost.conf.j2",
            domain=domain,
            document_root=str(self.www_root / domain / "public_html"),
            access_log=str(self.www_root / domain / "logs" / "access.log"),
            error_log=str(self.www_root / domain / "logs" / "error.log"),
            cert_path=cert_path,
            key_path=key_path,
            chain_path=chain_path,
            force_https=force_https,
            site_type=site_type,
            php_version=php_version,
            proxy_port=proxy_port,
            proxy_address=proxy_address,
        )

        config_path = self.sites_available / f"{domain}.conf"
        await run_sudo(f"bash -c 'cat > {config_path} << \"NGXEOF\"\n{config}\nNGXEOF'", shell=True)

        test_result = await self.test_config()
        if test_result["success"]:
            await self.reload()
            return {"success": True}
        return {"success": False, "error": test_result["error"]}


# Singleton
nginx_service = NginxService()
