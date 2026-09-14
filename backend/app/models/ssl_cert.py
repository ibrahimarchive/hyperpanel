"""SSL certificate model."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Boolean
from app.database import Base


class CertType(str, enum.Enum):
    LETS_ENCRYPT = "letsencrypt"
    CUSTOM = "custom"
    SELF_SIGNED = "self_signed"


class CertStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"
    REVOKED = "revoked"
    ERROR = "error"


class SSLCertificate(Base):
    __tablename__ = "ssl_certificates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=True)
    
    domain_name = Column(String(255), nullable=False)
    cert_type = Column(Enum(CertType), default=CertType.LETS_ENCRYPT, nullable=False)
    status = Column(Enum(CertStatus), default=CertStatus.PENDING, nullable=False)
    
    # Certificate paths
    cert_path = Column(String(512), nullable=True)
    key_path = Column(String(512), nullable=True)
    chain_path = Column(String(512), nullable=True)
    
    # Certificate details
    issuer = Column(String(255), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Auto-renewal
    auto_renew = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SSLCertificate {self.domain_name} ({self.status.value})>"
