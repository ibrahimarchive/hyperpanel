"""Backup model."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, BigInteger, Text
from app.database import Base


class BackupType(str, enum.Enum):
    FULL = "full"
    WEBSITE = "website"
    DATABASE = "database"
    FILES = "files"


class BackupStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Backup(Base):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    backup_type = Column(Enum(BackupType), nullable=False)
    status = Column(Enum(BackupStatus), default=BackupStatus.PENDING, nullable=False)
    
    # What's included
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=True)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=True)
    
    # File info
    filename = Column(String(255), nullable=True)
    filepath = Column(String(512), nullable=True)
    size_bytes = Column(BigInteger, default=0)
    
    # Details
    description = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Backup {self.backup_type.value} ({self.status.value})>"
