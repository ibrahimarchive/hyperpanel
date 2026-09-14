"""Database and database user models for MySQL/MariaDB management."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from app.database import Base


class Database(Base):
    __tablename__ = "databases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(64), unique=True, nullable=False, index=True)
    charset = Column(String(32), default="utf8mb4")
    collation = Column(String(64), default="utf8mb4_unicode_ci")
    size_bytes = Column(BigInteger, default=0)
    
    # Associated website (optional)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Database {self.name}>"


class DatabaseUser(Base):
    __tablename__ = "database_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    username = Column(String(32), unique=True, nullable=False)
    host = Column(String(64), default="localhost")
    
    # Comma-separated list of database IDs this user has access to
    database_ids = Column(String(512), default="")
    
    # Privileges (stored as comma-separated: ALL, SELECT, INSERT, UPDATE, DELETE, etc.)
    privileges = Column(String(512), default="ALL")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DatabaseUser {self.username}@{self.host}>"
