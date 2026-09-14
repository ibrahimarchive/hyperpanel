"""Website model for managed web applications."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text
from app.database import Base


class WebsiteType(str, enum.Enum):
    PHP = "php"
    NODEJS = "nodejs"
    PYTHON = "python"
    STATIC = "static"
    REVERSE_PROXY = "reverse_proxy"


class WebsiteStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"
    CREATING = "creating"
    ERROR = "error"


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Basic info
    name = Column(String(128), nullable=False)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    site_type = Column(Enum(WebsiteType), default=WebsiteType.PHP, nullable=False)
    status = Column(Enum(WebsiteStatus), default=WebsiteStatus.ACTIVE, nullable=False)
    
    # Paths
    document_root = Column(String(512), nullable=False)
    access_log = Column(String(512), nullable=True)
    error_log = Column(String(512), nullable=True)
    
    # PHP settings
    php_version = Column(String(8), default="8.2", nullable=True)
    
    # Proxy settings (for Node.js/Python apps)
    proxy_port = Column(Integer, nullable=True)
    proxy_address = Column(String(255), default="127.0.0.1", nullable=True)
    
    # SSL
    ssl_enabled = Column(Boolean, default=False)
    force_https = Column(Boolean, default=False)
    
    # Git deployment
    git_repo = Column(String(512), nullable=True)
    git_branch = Column(String(128), default="main", nullable=True)
    auto_deploy = Column(Boolean, default=False)
    
    # Notes
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Website {self.domain} ({self.site_type.value})>"
