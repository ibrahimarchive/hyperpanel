"""
User management service.
"""

import logging
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


class UserService:
    """Manages panel user accounts."""

    async def create_user(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        role: str = "user",
        full_name: Optional[str] = None,
        **limits,
    ) -> User:
        """Create a new panel user."""
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole(role),
            full_name=full_name,
            **limits,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        logger.info(f"User '{username}' created with role '{role}'")
        return user

    async def get_users(self, db: AsyncSession, skip: int = 0, limit: int = 50) -> List[User]:
        """List all users."""
        result = await db.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def get_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get a user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def update_user(self, db: AsyncSession, user_id: int, **kwargs) -> Optional[User]:
        """Update a user's profile."""
        user = await self.get_user(db, user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                if key == "role":
                    value = UserRole(value)
                setattr(user, key, value)

        await db.flush()
        await db.refresh(user)
        return user

    async def change_password(self, db: AsyncSession, user_id: int, new_password: str) -> bool:
        """Change a user's password."""
        user = await self.get_user(db, user_id)
        if not user:
            return False

        user.hashed_password = hash_password(new_password)
        await db.flush()
        return True

    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        """Delete a user."""
        user = await self.get_user(db, user_id)
        if not user:
            return False

        await db.delete(user)
        await db.flush()
        logger.info(f"User '{user.username}' deleted")
        return True

    async def count_users(self, db: AsyncSession) -> int:
        """Count total users."""
        result = await db.execute(select(func.count(User.id)))
        return result.scalar() or 0


# Singleton
user_service = UserService()
