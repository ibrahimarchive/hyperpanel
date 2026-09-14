"""Domain model for tracking registered domains."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Date
from app.database import Base


class DomainStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(Enum(DomainStatus), default=DomainStatus.ACTIVE, nullable=False)
    
    # Optional registrar info
    registrar = Column(String(128), nullable=True)
    expiry_date = Column(Date, nullable=True)
    nameservers = Column(String(512), nullable=True)  # Comma-separated
    
    # DNS zone management
    dns_managed = Column(String(10), default="local")  # local, external
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Domain {self.name}>"
