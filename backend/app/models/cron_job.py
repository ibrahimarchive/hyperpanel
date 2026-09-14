"""Cron job model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from app.database import Base


class CronJob(Base):
    __tablename__ = "cron_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Cron schedule (5 fields: minute hour day month weekday)
    schedule = Column(String(64), nullable=False)
    command = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    
    # Status
    enabled = Column(Boolean, default=True)
    
    # Execution tracking
    last_run = Column(DateTime, nullable=True)
    last_status = Column(String(16), nullable=True)  # success, failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CronJob {self.schedule} — {self.command[:30]}>"
