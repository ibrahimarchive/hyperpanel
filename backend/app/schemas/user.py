"""User schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"
    full_name: Optional[str] = None
    max_websites: int = 10
    max_databases: int = 10
    max_domains: int = 10
    disk_quota_mb: int = 5120
    bandwidth_quota_mb: int = 102400


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    max_websites: Optional[int] = None
    max_databases: Optional[int] = None
    max_domains: Optional[int] = None
    disk_quota_mb: Optional[int] = None
    bandwidth_quota_mb: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    full_name: Optional[str] = None
    max_websites: int
    max_databases: int
    max_domains: int
    disk_quota_mb: int
    bandwidth_quota_mb: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
