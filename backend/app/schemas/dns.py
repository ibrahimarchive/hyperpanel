"""DNS record schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DNSRecordCreate(BaseModel):
    domain_id: int
    record_type: str  # A, AAAA, CNAME, MX, TXT, NS, SRV, CAA
    name: str
    value: str
    ttl: int = 3600
    priority: Optional[int] = None


class DNSRecordUpdate(BaseModel):
    record_type: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None
    ttl: Optional[int] = None
    priority: Optional[int] = None


class DNSRecordResponse(BaseModel):
    id: int
    domain_id: int
    record_type: str
    name: str
    value: str
    ttl: int
    priority: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
