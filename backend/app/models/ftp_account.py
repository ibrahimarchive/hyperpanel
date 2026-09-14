"""FTP Account model for Pure-FTPd virtual users."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from app.database import Base


class FTPAccountStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class FTPAccount(Base):
    __tablename__ = "ftp_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # FTP login username (virtual user in PureDB)
    username = Column(String(64), unique=True, nullable=False, index=True)

    # Chrooted directory for this user (e.g. /var/www/example.com)
    directory = Column(String(512), nullable=False)

    # Quota in Megabytes (0 = unlimited)
    quota_mb = Column(Integer, default=0, nullable=False)

    # Account status
    status = Column(Enum(FTPAccountStatus), default=FTPAccountStatus.ACTIVE, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
