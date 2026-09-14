"""SSL certificate schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SSLIssueRequest(BaseModel):
    domain_name: str
    website_id: Optional[int] = None
    auto_renew: bool = True


class SSLUploadRequest(BaseModel):
    domain_name: str
    certificate: str  # PEM content
    private_key: str  # PEM content
    chain: Optional[str] = None  # CA bundle PEM content
    website_id: Optional[int] = None


class SSLResponse(BaseModel):
    id: int
    domain_name: str
    cert_type: str
    status: str
    issuer: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    auto_renew: bool
    created_at: datetime

    class Config:
        from_attributes = True
