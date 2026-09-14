"""Activity log model for auditing all panel actions."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Action details
    action = Column(String(64), nullable=False)  # e.g., "website.create", "ssl.issue"
    category = Column(String(32), nullable=False)  # e.g., "website", "ssl", "auth"
    description = Column(Text, nullable=False)
    
    # Context
    resource_type = Column(String(32), nullable=True)  # e.g., "website", "database"
    resource_id = Column(Integer, nullable=True)
    resource_name = Column(String(255), nullable=True)
    
    # Request info
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    
    # Status
    status = Column(String(16), default="success")  # success, failed, warning
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ActivityLog {self.action} ({self.status})>"
