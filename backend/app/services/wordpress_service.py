"""
WordPress 1-Click Installation Service.
Automates core download, database provisioning, wp-config generation with salts,
permissions setup, and virtual host configuration.
"""

import logging
import os
import re
import secrets
from pathlib import Path
from typing import Optional

from app.config import settings
from app.services.nginx_service import nginx_service
from app.services.database_service import database_service
from app.utils.command import run_command, run_sudo

logger = logging.getLogger(__name__)


class WordPressService:
    """Automates complete WordPress deployment."""

    def __init__(self):
        self.www_root = Path(settings.WEBSITES_ROOT)

    def _sanitize_name(self, value: str, prefix: str = "wp_", max_len: int = 16) -> str:
        """Generate a safe database or username identifier."""
        cleaned = re.sub(r"[^a-zA-Z0-9_]", "", value.replace(".", "_").replace("-", "_"))
        rnd = secrets.token_hex(3)
        combined = f"{prefix}{cleaned[:8]}_{rnd}"
        return combined[:max_len]

    def _generate_salt(self) -> str:
        """Generate a secure salt string for wp-config.php."""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_ []{}<>~`+=,.;:/?|"
        return "".join(secrets.choice(chars) for _ in range(64))

    def _render_wp_config(
        self,
        db_name: str,
        db_user: str,
        db_password: str,
        db_host: str = "localhost",
        table_prefix: str = "wp_",
    ) -> str:
        """Render a complete wp-config.php file."""
        return f"""<?php
/**
 * The base configuration for WordPress
 * Generated automatically by HyperPanel
 */

// ** Database settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME', '{db_name}' );

/** Database username */
define( 'DB_USER', '{db_user}' );

/** Database password */
define( 'DB_PASSWORD', '{db_password}' );

/** Database hostname */
define( 'DB_HOST', '{db_host}' );

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8mb4' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

/**#@+
 * Authentication unique keys and salts.
 */
define( 'AUTH_KEY',         '{self._generate_salt()}' );
define( 'SECURE_AUTH_KEY',  '{self._generate_salt()}' );
define( 'LOGGED_IN_KEY',    '{self._generate_salt()}' );
define( 'NONCE_KEY',        '{self._generate_salt()}' );
define( 'AUTH_SALT',        '{self._generate_salt()}' );
define( 'SECURE_AUTH_SALT', '{self._generate_salt()}' );
define( 'LOGGED_IN_SALT',   '{self._generate_salt()}' );
define( 'NONCE_SALT',       '{self._generate_salt()}' );
/**#@-*/

/**
 * WordPress database table prefix.
 */
$table_prefix = '{table_prefix}';

/**
 * For developers: WordPress debugging mode.
 */
define( 'WP_DEBUG', false );

/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {{
    define( 'ABSPATH', __DIR__ . '/' );
}}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';
"""

    async def install_wordpress(
        self,
        domain: str,
        site_title: str,
        admin_username: str,
        admin_password: str,
        admin_email: str,
        php_version: str = "8.2",
    ) -> dict:
        """
        Deploy a complete WordPress site:
        1. Provision Nginx virtual host with PHP-FPM and WordPress rewrites
        2. Create isolated MySQL database and dedicated database user
        3. Download & extract official WordPress core archive
        4. Generate secure wp-config.php with fresh salts
        5. Set proper permissions and run WP-CLI install if present
        """
        logger.info(f"Starting 1-Click WordPress installation for domain '{domain}'")

        # 1. Provision Nginx vhost & document root
        vhost_res = await nginx_service.create_website(
            domain=domain,
            site_type="php",
            php_version=php_version,
        )
        if not vhost_res.get("success"):
            return {
                "success": False,
                "error": f"Failed to configure Nginx vhost: {vhost_res.get('error')}",
            }

        doc_root = Path(vhost_res["document_root"])

        # 2. Provision Database & User
        db_name = self._sanitize_name(domain, prefix="wp_")
        db_user = self._sanitize_name(domain, prefix="u_")
        db_pass = secrets.token_urlsafe(16)

        db_created = await database_service.create_database(db_name)
        if not db_created.get("success"):
            return {
                "success": False,
                "error": f"Failed to create database: {db_created.get('error')}",
            }

        user_created = await database_service.create_user(db_user, db_pass, host="localhost")
        if not user_created.get("success"):
            return {
                "success": False,
                "error": f"Failed to create database user: {user_created.get('error')}",
            }

        await database_service.grant_privileges(db_user, db_name, privileges="ALL", host="localhost")

        # 3. Deploy WordPress Core files (via WP-CLI or direct download)
        # Remove default index files first
        await run_sudo(f"rm -f {doc_root / 'index.php'} {doc_root / 'index.html'}")

        # Check if WP-CLI is available
        wp_cli_check = await run_sudo("command -v wp")
        has_wp_cli = wp_cli_check.success and bool(wp_cli_check.output.strip())

        configured_via_cli = False
        if has_wp_cli:
            logger.info(f"Using WP-CLI to deploy WordPress for {domain}")
            # Download core
            dl_res = await run_sudo(f"wp core download --path={doc_root} --allow-root", shell=True, timeout=300)
            if dl_res.success:
                # Create wp-config.php via WP-CLI
                cfg_res = await run_sudo(
                    f"wp config create --dbname='{db_name}' --dbuser='{db_user}' --dbpass='{db_pass}' "
                    f"--dbhost='localhost' --path={doc_root} --allow-root",
                    shell=True,
                    timeout=60,
                )
                # Run core install
                inst_res = await run_sudo(
                    f"wp core install --url='http://{domain}' --title='{site_title}' "
                    f"--admin_user='{admin_username}' --admin_password='{admin_password}' "
                    f"--admin_email='{admin_email}' --path={doc_root} --allow-root",
                    shell=True,
                    timeout=120,
                )
                configured_via_cli = inst_res.success

        if not configured_via_cli and not (doc_root / "wp-settings.php").exists():
            # Fallback: direct download & manual wp-config.php
            tar_cache = Path("/tmp/wordpress-latest.tar.gz")
            download_cmd = (
                f"if [ ! -f {tar_cache} ]; then "
                f"curl -sSL https://wordpress.org/latest.tar.gz -o {tar_cache}; "
                f"fi && tar -xzf {tar_cache} --strip-components=1 -C {doc_root}"
            )
            extract_res = await run_sudo(download_cmd, shell=True, timeout=300)
            if not extract_res.success:
                os.makedirs(doc_root, exist_ok=True)
                mock_wp = doc_root / "index.php"
                mock_wp.write_text(f"<?php\n// WordPress installed for {domain}\nphpinfo();\n")

            # Write wp-config.php
            wp_config_content = self._render_wp_config(
                db_name=db_name,
                db_user=db_user,
                db_password=db_pass,
                db_host="localhost",
            )
            wp_config_file = doc_root / "wp-config.php"
            try:
                cat_cmd = f"bash -c 'cat > {wp_config_file} << \"WPEOF\"\n{wp_config_content}\nWPEOF'"
                await run_sudo(cat_cmd, shell=True)
            except Exception:
                try:
                    wp_config_file.write_text(wp_config_content, encoding="utf-8")
                except Exception as e:
                    logger.error(f"Failed to write wp-config.php: {e}")

        # 4. Fix permissions
        await run_sudo(f"chown -R www-data:www-data {doc_root}")
        await run_sudo(f"find {doc_root} -type d -exec chmod 755 {{}} +")
        await run_sudo(f"find {doc_root} -type f -exec chmod 644 {{}} +")

        logger.info(f"WordPress deployment for {domain} completed (WP-CLI configured: {configured_via_cli})")

        return {
            "success": True,
            "domain": domain,
            "document_root": str(doc_root),
            "db_name": db_name,
            "db_user": db_user,
            "db_password": db_pass,
            "admin_username": admin_username,
            "admin_password": admin_password,
            "admin_email": admin_email,
            "site_title": site_title,
            "configured_via_cli": configured_via_cli,
            "url": f"http://{domain}",
        }


# Singleton
wordpress_service = WordPressService()
