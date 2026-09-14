"""Firewall rule model."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.database import Base


class RuleAction(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"
    LIMIT = "limit"


class RuleProtocol(str, enum.Enum):
    TCP = "tcp"
    UDP = "udp"
    BOTH = "both"


class FirewallRule(Base):
    __tablename__ = "firewall_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    action = Column(Enum(RuleAction), nullable=False)
    protocol = Column(Enum(RuleProtocol), default=RuleProtocol.TCP, nullable=False)
    port = Column(String(16), nullable=False)  # Single port or range "80" or "8000:8100"
    source_ip = Column(String(64), nullable=True)  # Null = any
    description = Column(String(255), nullable=True)
    
    # Whether this rule is managed by HyperPanel (vs pre-existing)
    managed = Column(String(10), default="yes")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FirewallRule {self.action.value} {self.port}/{self.protocol.value}>"
