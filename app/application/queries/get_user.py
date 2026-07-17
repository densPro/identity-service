"""Get User query."""

from __future__ import annotations

import uuid

from app.application.dtos.user_response import UserResponseDTO
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.domain.entities.user import User
from app.domain.exceptions import UserNotFoundError


class GetUserQuery:
    """Fetch a single user by ID or email."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def by_id(self, user_id: uuid.UUID) -> UserResponseDTO:
        """Return a user by UUID.

        Raises
        ------
        UserNotFoundError
            If no user exists for *user_id*.
        """
        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError(str(user_id))

        return self._to_dto(user)

    async def by_email(self, email: str) -> UserResponseDTO:
        """Return a user by email address.

        Raises
        ------
        UserNotFoundError
            If no user exists for *email*.
        """
        async with self._uow:
            user = await self._uow.users.get_by_email(email)

        if user is None:
            raise UserNotFoundError(email)

        return self._to_dto(user)

    @staticmethod
    def _to_dto(user: User) -> UserResponseDTO:
        return UserResponseDTO(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
