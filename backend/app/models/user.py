"""User model with role-based access control."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RESELLER = "reseller"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Two-Factor Authentication
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=False)

    # Profile
    full_name = Column(String(128), nullable=True)
    
    # System user mapping
    system_username = Column(String(32), nullable=True, unique=True)
    home_directory = Column(String(255), nullable=True)
    
    # Limits
    max_websites = Column(Integer, default=10)
    max_databases = Column(Integer, default=10)
    max_domains = Column(Integer, default=10)
    disk_quota_mb = Column(Integer, default=5120)  # 5 GB default
    bandwidth_quota_mb = Column(Integer, default=102400)  # 100 GB default
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"
