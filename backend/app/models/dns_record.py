"""DNS record model."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from app.database import Base


class RecordType(str, enum.Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"
    SRV = "SRV"
    CAA = "CAA"
    PTR = "PTR"


class DNSRecord(Base):
    __tablename__ = "dns_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, index=True)
    
    record_type = Column(Enum(RecordType), nullable=False)
    name = Column(String(255), nullable=False)  # subdomain or @ for root
    value = Column(String(1024), nullable=False)  # IP, hostname, text, etc.
    ttl = Column(Integer, default=3600)
    priority = Column(Integer, nullable=True)  # For MX and SRV records
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DNSRecord {self.record_type.value} {self.name} -> {self.value}>"
