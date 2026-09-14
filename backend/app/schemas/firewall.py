"""Firewall rule schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FirewallRuleCreate(BaseModel):
    action: str  # allow, deny, limit
    protocol: str = "tcp"  # tcp, udp, both
    port: str
    source_ip: Optional[str] = None
    description: Optional[str] = None


class FirewallRuleResponse(BaseModel):
    id: int
    action: str
    protocol: str
    port: str
    source_ip: Optional[str] = None
    description: Optional[str] = None
    managed: str
    created_at: datetime

    class Config:
        from_attributes = True


class FirewallStatusResponse(BaseModel):
    enabled: bool
    default_incoming: str
    default_outgoing: str
    rules_count: int
