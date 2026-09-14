"""
TOTP Two-Factor Authentication service.
"""

import base64
import hashlib
import hmac
import io
import logging
import secrets
import struct
import time

logger = logging.getLogger(__name__)

# TOTP constants
TOTP_DIGITS = 6
TOTP_PERIOD = 30
TOTP_ISSUER = "HyperPanel"


class TOTPService:
    """Manages TOTP-based two-factor authentication."""

    def generate_secret(self) -> str:
        """Generate a random TOTP secret (base32 encoded)."""
        secret_bytes = secrets.token_bytes(20)
        return base64.b32encode(secret_bytes).decode("utf-8").rstrip("=")

    def get_provisioning_uri(self, secret: str, username: str) -> str:
        """Generate an otpauth:// URI for QR code scanning."""
        # Pad secret for base32
        padded = secret + "=" * ((8 - len(secret) % 8) % 8)
        return (
            f"otpauth://totp/{TOTP_ISSUER}:{username}"
            f"?secret={secret}&issuer={TOTP_ISSUER}&digits={TOTP_DIGITS}&period={TOTP_PERIOD}"
        )

    def generate_qr_data_uri(self, provisioning_uri: str) -> str:
        """Generate a QR code as a base64 data URI.
        Falls back to returning the URI if qrcode package is not installed.
        """
        try:
            import qrcode
            import qrcode.image.svg

            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64}"
        except ImportError:
            logger.warning("qrcode package not installed — returning provisioning URI only")
            return provisioning_uri

    def verify_code(self, secret: str, code: str, window: int = 1) -> bool:
        """Verify a TOTP code. Allows a window of +/- periods for clock skew."""
        if not code or len(code) != TOTP_DIGITS:
            return False

        try:
            code_int = int(code)
        except ValueError:
            return False

        # Pad secret for base32 decoding
        padded = secret + "=" * ((8 - len(secret) % 8) % 8)
        try:
            key = base64.b32decode(padded.upper())
        except Exception:
            return False

        current_time = int(time.time())

        for offset in range(-window, window + 1):
            counter = (current_time // TOTP_PERIOD) + offset
            expected = self._generate_totp(key, counter)
            if hmac.compare_digest(str(expected).zfill(TOTP_DIGITS), str(code_int).zfill(TOTP_DIGITS)):
                return True

        return False

    def _generate_totp(self, key: bytes, counter: int) -> int:
        """Generate a TOTP code for a given counter value."""
        # Pack counter as big-endian 8-byte
        counter_bytes = struct.pack(">Q", counter)

        # HMAC-SHA1
        h = hmac.new(key, counter_bytes, hashlib.sha1).digest()

        # Dynamic truncation
        offset = h[-1] & 0x0F
        truncated = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF

        return truncated % (10 ** TOTP_DIGITS)

    def generate_recovery_codes(self, count: int = 8) -> list[str]:
        """Generate backup recovery codes."""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes


# Singleton
totp_service = TOTPService()
