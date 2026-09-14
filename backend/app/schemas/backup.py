"""Backup and cron schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BackupCreate(BaseModel):
    backup_type: str = "full"  # full, website, database, files
    website_id: Optional[int] = None
    database_id: Optional[int] = None
    description: Optional[str] = None


class BackupResponse(BaseModel):
    id: int
    user_id: int
    backup_type: str
    status: str
    website_id: Optional[int] = None
    database_id: Optional[int] = None
    filename: Optional[str] = None
    size_bytes: int
    description: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CronJobCreate(BaseModel):
    schedule: str
    command: str
    description: Optional[str] = None
    enabled: bool = True


class CronJobUpdate(BaseModel):
    schedule: Optional[str] = None
    command: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class CronJobResponse(BaseModel):
    id: int
    user_id: int
    schedule: str
    command: str
    description: Optional[str] = None
    enabled: bool
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
