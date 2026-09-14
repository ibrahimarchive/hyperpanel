"""URL Redirect model for website redirection rules."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Redirect(Base):
    __tablename__ = "redirects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    source_path = Column(String(255), nullable=False)  # e.g. "/blog/old-post"
    target_url = Column(String(512), nullable=False)   # e.g. "https://example.com/new-post" or "/new-path"
    redirect_type = Column(Integer, default=301, nullable=False)  # 301 (Permanent) or 302 (Temporary)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    website = relationship("Website", backref="redirects")

    def __repr__(self):
        return f"<Redirect {self.source_path} -> {self.target_url} ({self.redirect_type})>"
