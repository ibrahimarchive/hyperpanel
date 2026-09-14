"""Domain schemas."""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class DomainCreate(BaseModel):
    name: str
    registrar: Optional[str] = None
    expiry_date: Optional[date] = None
    nameservers: Optional[str] = None
    dns_managed: str = "local"


class DomainUpdate(BaseModel):
    registrar: Optional[str] = None
    expiry_date: Optional[date] = None
    nameservers: Optional[str] = None
    dns_managed: Optional[str] = None
    status: Optional[str] = None


class DomainResponse(BaseModel):
    id: int
    user_id: int
    name: str
    status: str
    registrar: Optional[str] = None
    expiry_date: Optional[date] = None
    nameservers: Optional[str] = None
    dns_managed: str
    created_at: datetime

    class Config:
        from_attributes = True
