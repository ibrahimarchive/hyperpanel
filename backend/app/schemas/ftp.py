"""FTP Account schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FTPAccountCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=6, max_length=128)
    directory: str = Field(..., min_length=1, max_length=512)
    quota_mb: Optional[int] = Field(default=0, ge=0)


class FTPAccountUpdate(BaseModel):
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    directory: Optional[str] = Field(default=None, min_length=1, max_length=512)
    quota_mb: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None, pattern=r"^(active|suspended)$")


class FTPAccountResponse(BaseModel):
    id: int
    user_id: int
    username: str
    directory: str
    quota_mb: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
