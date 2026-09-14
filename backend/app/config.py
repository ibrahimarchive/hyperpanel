"""
HyperPanel Configuration
Centralized settings management using pydantic-settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Panel Access & SSL
    PANEL_DOMAIN: str = ""
    PANEL_SSL_ENABLED: bool = True
    PANEL_SSL_CERT: str = ""
    PANEL_SSL_KEY: str = ""

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./hyperpanel.db"

    # Server
    PANEL_HOST: str = "0.0.0.0"
    PANEL_PORT: int = 8443
    DEBUG: bool = False

    # Allowed hosts
    ALLOWED_HOSTS: str = "*"

    # Admin setup
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@localhost"
    ADMIN_PASSWORD: str = "changeme"

    # Paths
    WEBSITES_ROOT: str = "/var/www"
    NGINX_SITES_DIR: str = "/etc/nginx/sites-available"
    NGINX_SITES_ENABLED: str = "/etc/nginx/sites-enabled"
    BACKUPS_DIR: str = "/var/hyperpanel/backups"
    SSL_CERTS_DIR: str = "/etc/letsencrypt/live"

    # Panel info
    PANEL_NAME: str = "HyperPanel"
    PANEL_VERSION: str = "1.0.0"

    @property
    def websites_root_path(self) -> Path:
        return Path(self.WEBSITES_ROOT)

    @property
    def backups_path(self) -> Path:
        return Path(self.BACKUPS_DIR)


settings = Settings()
