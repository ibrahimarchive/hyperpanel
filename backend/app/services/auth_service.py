"""
Authentication service.
Handles JWT tokens, password hashing, and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user: User) -> str:
    """Create a JWT access token for a user."""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value if isinstance(user.role, UserRole) else user.role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user: User) -> str:
    """Create a JWT refresh token for a user."""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user.id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_temp_2fa_token(user: User) -> str:
    """Create a short-lived token for 2FA challenge verification (5 mins)."""
    expire = datetime.utcnow() + timedelta(minutes=5)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": expire,
        "type": "2fa_pending",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    """Authenticate a user by username and password."""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        return None

    if not user.is_active:
        return None

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user by their ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_admin_user(db: AsyncSession) -> Optional[User]:
    """Create the initial admin user if none exists."""
    result = await db.execute(
        select(User).where(User.role == UserRole.ADMIN)
    )
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        return None  # Admin already exists

    admin = User(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        is_active=True,
        full_name="Administrator",
        max_websites=999,
        max_databases=999,
        max_domains=999,
        disk_quota_mb=0,  # Unlimited
        bandwidth_quota_mb=0,  # Unlimited
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin
