"""
HyperPanel Settings & Network Management Service.
Handles Panel Domain, Panel Port, Firewall synchronization, and Panel SSL (Self-Signed & Custom PEM).
"""

import datetime
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.config import settings
from app.utils.command import run_sudo

logger = logging.getLogger(__name__)

# Settings file path
SETTINGS_FILE = Path(__file__).parent.parent.parent / "panel_settings.json"
SSL_DIR = Path(__file__).parent.parent.parent / "ssl"


class PanelSettingsService:
    """Manages panel network, access, and SSL configurations."""

    def __init__(self):
        self._load_settings()
        # Ensure SSL directory exists
        try:
            SSL_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _load_settings(self) -> dict:
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                    return self._data
            except Exception as e:
                logger.error(f"Error loading panel_settings.json: {e}")
        self._data = {
            "panel_port": settings.PANEL_PORT,
            "panel_domain": getattr(settings, "PANEL_DOMAIN", "") or "",
            "ssl_enabled": True,
            "ssl_cert_path": str(SSL_DIR / "panel.crt"),
            "ssl_key_path": str(SSL_DIR / "panel.key"),
        }
        self._save_settings()
        return self._data

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving panel_settings.json: {e}")

    def _update_env_file(self, updates: dict):
        """Update key-value pairs in backend/.env file."""
        env_path = Path(__file__).parent.parent.parent / ".env"
        if not env_path.exists():
            return

        try:
            lines = env_path.read_text(encoding="utf-8").splitlines()
            new_lines = []
            keys_seen = set()

            for line in lines:
                stripped = line.strip()
                if "=" in stripped and not stripped.startswith("#"):
                    k = stripped.split("=", 1)[0].strip()
                    if k in updates:
                        new_lines.append(f"{k}={updates[k]}")
                        keys_seen.add(k)
                        continue
                new_lines.append(line)

            for k, v in updates.items():
                if k not in keys_seen:
                    new_lines.append(f"{k}={v}")

            env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to update .env: {e}")

    def get_certificate_info(self) -> dict:
        """Parse panel SSL certificate and return status & validity metadata."""
        cert_path = Path(self._data.get("ssl_cert_path", str(SSL_DIR / "panel.crt")))

        # If certificate does not exist, create a default self-signed cert
        if not cert_path.exists() or cert_path.stat().st_size == 0:
            domain = self._data.get("panel_domain") or "127.0.0.1"
            self.generate_self_signed_cert(domain=domain)

        try:
            cert_bytes = cert_path.read_bytes()
            cert = x509.load_pem_x509_certificate(cert_bytes)

            common_name = ""
            for attr in cert.subject:
                if attr.oid == NameOID.COMMON_NAME:
                    common_name = attr.value
                    break

            issuer_name = "HyperPanel CA"
            for attr in cert.issuer:
                if attr.oid in (NameOID.ORGANIZATION_NAME, NameOID.COMMON_NAME):
                    issuer_name = attr.value
                    break

            now = datetime.datetime.now(datetime.timezone.utc)
            not_before = cert.not_valid_before_utc
            not_after = cert.not_valid_after_utc

            total_days = max(1, (not_after - not_before).days)
            days_remaining = max(0, (not_after - now).days)
            days_passed = max(0, total_days - days_remaining)
            validity_percent = max(0, min(100, int((days_remaining / total_days) * 100)))

            is_trusted = "Let's Encrypt" in issuer_name or "DigiCert" in issuer_name or "Cloudflare" in issuer_name
            status = "Trusted" if is_trusted else "Self-signed"

            return {
                "installed": True,
                "enabled": self._data.get("ssl_enabled", True),
                "status": status,
                "domain": common_name or self._data.get("panel_domain") or "127.0.0.1",
                "issuer": issuer_name,
                "expiration_date": not_after.strftime("%Y-%m-%d"),
                "days_remaining": days_remaining,
                "days_passed": days_passed,
                "total_days": total_days,
                "validity_percent": validity_percent,
                "cert_path": str(cert_path),
            }
        except Exception as e:
            logger.error(f"Error parsing SSL certificate: {e}")
            return {
                "installed": False,
                "enabled": self._data.get("ssl_enabled", False),
                "status": "Disabled",
                "domain": self._data.get("panel_domain") or "127.0.0.1",
                "issuer": "None",
                "expiration_date": "—",
                "days_remaining": 0,
                "days_passed": 0,
                "total_days": 365,
                "validity_percent": 0,
                "cert_path": str(cert_path),
            }

    def generate_self_signed_cert(self, domain: str = "127.0.0.1") -> dict:
        """Generate a 10-year (3650 days) self-signed SSL certificate for the panel."""
        cert_path = Path(self._data.get("ssl_cert_path", str(SSL_DIR / "panel.crt")))
        key_path = Path(self._data.get("ssl_key_path", str(SSL_DIR / "panel.key")))

        cert_path.parent.mkdir(parents=True, exist_ok=True)

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, domain),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HyperPanel Authority"),
        ])

        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=3650))
            .sign(key, hashes.SHA256())
        )

        key_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        cert_bytes = cert.public_bytes(serialization.Encoding.PEM)

        key_path.write_bytes(key_bytes)
        cert_path.write_bytes(cert_bytes)

        self._data["ssl_enabled"] = True
        self._save_settings()

        return self.get_certificate_info()

    async def sync_nginx_config(self) -> bool:
        """Write /etc/nginx/sites-available/hyperpanel.conf and reload Nginx."""
        panel_port = self._data.get("panel_port", settings.PANEL_PORT)
        panel_domain = self._data.get("panel_domain", "")
        ssl_enabled = self._data.get("ssl_enabled", True)
        cert_path = self._data.get("ssl_cert_path", str(SSL_DIR / "panel.crt"))
        key_path = self._data.get("ssl_key_path", str(SSL_DIR / "panel.key"))

        # Ensure certificate exists if SSL is enabled
        if ssl_enabled and (not os.path.exists(cert_path) or os.path.getsize(cert_path) == 0):
            domain = panel_domain or "127.0.0.1"
            self.generate_self_signed_cert(domain=domain)

        # Build Nginx server block for the custom port
        if ssl_enabled and os.path.exists(cert_path):
            ssl_directives = f"""listen {panel_port} ssl default_server;
    ssl_certificate {cert_path};
    ssl_certificate_key {key_path};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    error_page 497 301 = https://$host:$server_port$request_uri;"""
        else:
            ssl_directives = f"""listen {panel_port} default_server;"""

        # Domain block if domain is bound
        domain_block = ""
        if panel_domain:
            if ssl_enabled and os.path.exists(cert_path):
                domain_block = f"""
server {{
    listen 80;
    listen 443 ssl;
    server_name {panel_domain};

    ssl_certificate {cert_path};
    ssl_certificate_key {key_path};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 500M;

        location / {{
            proxy_pass http://127.0.0.1:{settings.PANEL_INTERNAL_PORT};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400s;
            proxy_send_timeout 86400s;
        }}
    }}
    """
            else:
                domain_block = f"""
    server {{
        listen 80;
        server_name {panel_domain};

        client_max_body_size 500M;

        location / {{
            proxy_pass http://127.0.0.1:{settings.PANEL_INTERNAL_PORT};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400s;
            proxy_send_timeout 86400s;
        }}
    }}
    """

        nginx_conf = f"""# HyperPanel Management Server — Nginx Proxy
    server {{
        {ssl_directives}
        server_name _;

        client_max_body_size 500M;

        location / {{
            proxy_pass http://127.0.0.1:{settings.PANEL_INTERNAL_PORT};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400s;
            proxy_send_timeout 86400s;
        }}
    }}
    {domain_block}
    """
        try:
            conf_path = "/etc/nginx/sites-available/hyperpanel.conf"
            enabled_path = "/etc/nginx/sites-enabled/hyperpanel.conf"
            cat_cmd = f"bash -c 'cat > {conf_path} << \"NGXEOF\"\n{nginx_conf}\nNGXEOF'"
            await run_sudo(cat_cmd, shell=True)
            await run_sudo(f"ln -sf {conf_path} {enabled_path}", shell=True)
            t_res = await run_sudo("nginx -t")
            if t_res.success:
                await run_sudo("systemctl reload nginx")
                return True
            else:
                logger.error(f"Nginx test failed: {t_res.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error syncing panel nginx config: {e}")
            return False

    async def set_custom_ssl(self, certificate_pem: str, private_key_pem: str) -> dict:
        """Validate and install custom PEM certificate and private key."""
        try:
            cert = x509.load_pem_x509_certificate(certificate_pem.encode("utf-8"))
            serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        except Exception as e:
            return {"success": False, "error": f"Invalid SSL Certificate or Private Key: {str(e)}"}

        cert_path = Path(self._data.get("ssl_cert_path", str(SSL_DIR / "panel.crt")))
        key_path = Path(self._data.get("ssl_key_path", str(SSL_DIR / "panel.key")))

        cert_path.parent.mkdir(parents=True, exist_ok=True)
        cert_path.write_text(certificate_pem.strip() + "\n", encoding="utf-8")
        key_path.write_text(private_key_pem.strip() + "\n", encoding="utf-8")

        self._data["ssl_enabled"] = True
        self._save_settings()
        await self.sync_nginx_config()

        info = self.get_certificate_info()
        return {"success": True, "certificate": info, "message": "SSL Certificate updated successfully"}

    async def toggle_ssl(self, enabled: bool) -> dict:
        """Toggle panel SSL on/off."""
        self._data["ssl_enabled"] = enabled
        self._save_settings()
        self._update_env_file({"PANEL_SSL_ENABLED": str(enabled)})
        await self.sync_nginx_config()
        return self.get_certificate_info()

    async def set_panel_domain(self, domain: str) -> dict:
        """Set or clear the domain bound to the panel and attempt automatic Let's Encrypt SSL issuance."""
        domain = domain.strip().lower()
        if domain:
            if not re.match(r"^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$", domain) and domain != "localhost":
                return {"success": False, "error": "Invalid domain format (e.g. panel.example.com)"}

        self._data["panel_domain"] = domain
        self._save_settings()
        self._update_env_file({"PANEL_DOMAIN": domain})

        le_success = False
        le_error = None

        if domain and domain != "localhost":
            # Attempt automatic Let's Encrypt certificate issuance
            logger.info(f"Attempting automatic Let's Encrypt SSL issuance for panel domain '{domain}'")
            le_res = await self.issue_letsencrypt_panel()
            if le_res.get("success"):
                le_success = True
            else:
                le_error = le_res.get("error")
                # Fallback to self-signed cert if LE fails (e.g., DNS not propagated yet)
                cert_path = Path(self._data.get("ssl_cert_path", str(SSL_DIR / "panel.crt")))
                if not cert_path.exists() or cert_path.stat().st_size == 0:
                    self.generate_self_signed_cert(domain=domain)

        await self.sync_nginx_config()

        if domain:
            if le_success:
                msg = f"Panel domain set to '{domain}' and Let's Encrypt SSL certificate issued successfully!"
            elif le_error:
                msg = f"Panel domain set to '{domain}'. Let's Encrypt attempt note: {le_error}. Using self-signed SSL as fallback."
            else:
                msg = f"Panel domain set to '{domain}'"
        else:
            msg = "Panel domain un-bound (IP access allowed)"

        return {
            "success": True,
            "domain": domain,
            "letsencrypt_issued": le_success,
            "message": msg,
        }

    async def set_panel_port(self, port: int) -> dict:
        """Change the panel port and sync firewall rules."""
        if not (1024 <= port <= 65535):
            return {"success": False, "error": "Port must be between 1024 and 65535"}

        old_port = self._data.get("panel_port", settings.PANEL_PORT)
        self._data["panel_port"] = port
        self._save_settings()
        self._update_env_file({"PANEL_PORT": str(port)})

        # Automatically open new port in UFW
        try:
            await run_sudo(f"ufw allow {port}/tcp comment 'HyperPanel'")
        except Exception as e:
            logger.warning(f"Could not update firewall for port {port}: {e}")

        await self.sync_nginx_config()

        return {
            "success": True,
            "port": port,
            "old_port": old_port,
            "message": f"Panel port updated to {port}. Access via http(s)://<ip>:{port}",
        }

    async def issue_letsencrypt_panel(self, email: str = "") -> dict:
        """Issue a Let's Encrypt certificate for the panel domain and install it."""
        domain = self._data.get("panel_domain", "").strip()
        if not domain:
            return {"success": False, "error": "Set a panel domain first before requesting Let's Encrypt SSL."}

        from app.utils.validators import is_valid_acme_email

        # Run certbot
        email_flag = f"--email {email.strip()}" if email and is_valid_acme_email(email) else "--register-unsafely-without-email"
        cmd = (
            f"certbot certonly --nginx -d {domain} "
            f"{email_flag} --agree-tos --non-interactive --expand"
        )
        result = await run_sudo(cmd, timeout=120)

        if not result.success:
            return {
                "success": False,
                "error": f"Let's Encrypt issuance failed: {result.stderr or result.stdout}",
            }

        # Certbot stores certs here
        le_cert = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
        le_key = f"/etc/letsencrypt/live/{domain}/privkey.pem"

        # Update panel settings to use the LE cert
        self._data["ssl_cert_path"] = le_cert
        self._data["ssl_key_path"] = le_key
        self._data["ssl_enabled"] = True
        self._save_settings()

        await self.sync_nginx_config()

        info = self.get_certificate_info()
        return {
            "success": True,
            "certificate": info,
            "message": f"Let's Encrypt certificate issued and installed for panel domain '{domain}'",
        }

    def get_all_settings(self, username: str = "admin") -> dict:
        """Return full panel configuration for frontend consumption."""
        cert_info = self.get_certificate_info()
        return {
            "panel_port": self._data.get("panel_port", settings.PANEL_PORT),
            "panel_domain": self._data.get("panel_domain", ""),
            "panel_user": username,
            "ssl": cert_info,
        }


# Singleton
panel_settings_service = PanelSettingsService()
