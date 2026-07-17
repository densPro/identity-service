"""Abstract User Repository interface (port)."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.domain.entities.user import User


class IUserRepository(ABC):
    """Port defining the contract for user persistence operations."""

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return a User by primary key, or None if not found."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Return a User by email address, or None if not found."""
        ...

    @abstractmethod
    async def add(self, user: User) -> User:
        """Persist a new User and return it."""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """Persist changes to an existing User and return it."""
        ...
