"""Database management schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DatabaseCreate(BaseModel):
    name: str
    charset: str = "utf8mb4"
    collation: str = "utf8mb4_unicode_ci"
    website_id: Optional[int] = None


class DatabaseResponse(BaseModel):
    id: int
    user_id: int
    name: str
    charset: str
    collation: str
    size_bytes: int
    website_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DatabaseUserCreate(BaseModel):
    username: str
    password: str
    host: str = "localhost"
    database_ids: str = ""
    privileges: str = "ALL"


class DatabaseUserResponse(BaseModel):
    id: int
    user_id: int
    username: str
    host: str
    database_ids: str
    privileges: str
    created_at: datetime

    class Config:
        from_attributes = True
