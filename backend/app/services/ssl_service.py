"""
SSL certificate management service.
Handles Let's Encrypt issuance via certbot and custom certificate uploads.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from app.config import settings
from app.utils.command import run_sudo

logger = logging.getLogger(__name__)


class SSLService:
    """Manages SSL/TLS certificates."""

    async def issue_letsencrypt(self, domain: str, email: str = "") -> dict:
        """
        Issue a Let's Encrypt certificate using certbot.
        Uses the Nginx plugin for automatic verification and installation.
        """
        email_flag = f"--email {email}" if email else "--register-unsafely-without-email"
        cmd = (
            f"certbot certonly --nginx -d {domain} "
            f"{email_flag} --agree-tos --non-interactive --expand"
        )
        result = await run_sudo(cmd, timeout=120)

        if result.success:
            cert_dir = Path(settings.SSL_CERTS_DIR) / domain
            return {
                "success": True,
                "cert_path": str(cert_dir / "fullchain.pem"),
                "key_path": str(cert_dir / "privkey.pem"),
                "chain_path": str(cert_dir / "chain.pem"),
            }
        return {"success": False, "error": result.stderr}

    async def upload_certificate(
        self,
        domain: str,
        cert_content: str,
        key_content: str,
        chain_content: Optional[str] = None,
    ) -> dict:
        """Upload and install a custom SSL certificate safely using temp files."""
        cert_dir = Path(f"/etc/ssl/hyperpanel/{domain}")
        await run_sudo(f"mkdir -p {cert_dir}")

        cert_path = cert_dir / "cert.pem"
        key_path = cert_dir / "privkey.pem"

        # Write cert to temp file and move with sudo
        with tempfile.NamedTemporaryFile("w", delete=False) as tf_cert:
            tf_cert.write(cert_content.strip() + "\n")
            tmp_cert = tf_cert.name

        with tempfile.NamedTemporaryFile("w", delete=False) as tf_key:
            tf_key.write(key_content.strip() + "\n")
            tmp_key = tf_key.name

        try:
            await run_sudo(f"mv {tmp_cert} {cert_path}")
            await run_sudo(f"mv {tmp_key} {key_path}")
            await run_sudo(f"chmod 600 {key_path}")
        finally:
            await run_sudo(f"rm -f {tmp_cert} {tmp_key}")

        result = {
            "success": True,
            "cert_path": str(cert_path),
            "key_path": str(key_path),
        }

        if chain_content and chain_content.strip():
            chain_path = cert_dir / "chain.pem"
            with tempfile.NamedTemporaryFile("w", delete=False) as tf_chain:
                tf_chain.write(chain_content.strip() + "\n")
                tmp_chain = tf_chain.name
            try:
                await run_sudo(f"mv {tmp_chain} {chain_path}")
                result["chain_path"] = str(chain_path)
            finally:
                await run_sudo(f"rm -f {tmp_chain}")

        return result

    async def check_certificate(self, domain: str) -> dict:
        """Check SSL certificate details for a domain."""
        cmd = (
            f"echo | openssl s_client -servername {domain} -connect {domain}:443 2>/dev/null "
            f"| openssl x509 -noout -dates -subject -issuer 2>/dev/null"
        )
        result = await run_sudo(cmd, shell=True, timeout=15)

        if result.success:
            info = {}
            for line in result.stdout.split("\n"):
                if "notBefore" in line:
                    info["issued_at"] = line.split("=", 1)[1].strip()
                elif "notAfter" in line:
                    info["expires_at"] = line.split("=", 1)[1].strip()
                elif "subject" in line:
                    info["subject"] = line.split("=", 1)[1].strip()
                elif "issuer" in line:
                    info["issuer"] = line.split("=", 1)[1].strip()
            return {"success": True, **info}
        return {"success": False, "error": "Could not retrieve certificate info"}

    async def renew_certificates(self) -> dict:
        """Renew all Let's Encrypt certificates."""
        result = await run_sudo("certbot renew --non-interactive", timeout=300)
        return {"success": result.success, "output": result.stdout}

    async def revoke_certificate(self, domain: str) -> dict:
        """Revoke a Let's Encrypt certificate."""
        cert_path = Path(settings.SSL_CERTS_DIR) / domain / "fullchain.pem"
        result = await run_sudo(f"certbot revoke --cert-path {cert_path} --non-interactive")
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def delete_certificate(self, domain: str) -> dict:
        """Delete a certificate and its files."""
        result = await run_sudo(f"certbot delete --cert-name {domain} --non-interactive")
        # Also clean up custom certs
        await run_sudo(f"rm -rf /etc/ssl/hyperpanel/{domain}")
        return {"success": result.success}


# Singleton
ssl_service = SSLService()
