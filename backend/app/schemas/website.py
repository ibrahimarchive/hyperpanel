"""Website schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class WebsiteCreate(BaseModel):
    name: str
    domain: str
    site_type: str = "php"  # php, nodejs, python, static, reverse_proxy
    php_version: Optional[str] = "8.2"
    proxy_port: Optional[int] = None
    proxy_address: Optional[str] = "127.0.0.1"
    description: Optional[str] = None


class WordPressInstallRequest(BaseModel):
    domain: str
    site_title: str = "My WordPress Site"
    admin_username: str = "admin"
    admin_password: str
    admin_email: str
    php_version: Optional[str] = "8.2"
    description: Optional[str] = "WordPress Site"


class WebsiteUpdate(BaseModel):
    name: Optional[str] = None
    site_type: Optional[str] = None
    php_version: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_address: Optional[str] = None
    ssl_enabled: Optional[bool] = None
    force_https: Optional[bool] = None
    description: Optional[str] = None


class WebsiteResponse(BaseModel):
    id: int
    user_id: int
    name: str
    domain: str
    site_type: str
    status: str
    document_root: str
    php_version: Optional[str] = None
    proxy_port: Optional[int] = None
    ssl_enabled: bool
    force_https: bool
    git_repo: Optional[str] = None
    git_branch: Optional[str] = None
    auto_deploy: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
