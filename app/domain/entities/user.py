"""User domain entity — aggregate root."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.domain.enums.user_role import UserRole
from app.domain.enums.user_status import UserStatus


class User:
    """Pure Python User aggregate root.

    This class contains no SQLAlchemy or framework dependencies.
    """

    def __init__(
        self,
        id: uuid.UUID,
        email: str,
        hashed_password: str,
        first_name: str,
        last_name: str,
        role: UserRole,
        status: UserStatus = UserStatus.ACTIVE,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        email: str,
        hashed_password: str,
        first_name: str,
        last_name: str,
        role: UserRole,
    ) -> "User":
        """Build a brand-new User with auto-generated id and timestamps."""
        return cls(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            status=UserStatus.ACTIVE,
        )

    # ------------------------------------------------------------------
    # Domain behaviours
    # ------------------------------------------------------------------

    def is_active(self) -> bool:
        """Return True if the account is in ACTIVE status."""
        return self.status == UserStatus.ACTIVE

    def suspend(self) -> None:
        """Mark the account as suspended."""
        self.status = UserStatus.SUSPENDED

    def activate(self) -> None:
        """Re-activate a suspended or inactive account."""
        self.status = UserStatus.ACTIVE

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, email={self.email}, "
            f"role={self.role.value}, status={self.status.value})>"
        )
