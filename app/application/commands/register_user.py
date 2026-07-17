"""Register User command."""

from __future__ import annotations

from app.application.dtos.user_register import UserRegisterDTO
from app.application.dtos.user_response import UserResponseDTO
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.core.security import hash_password
from app.domain.entities.user import User
from app.domain.exceptions import DuplicateUserError


class RegisterUserCommand:
    """Orchestrates new user registration."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: UserRegisterDTO) -> UserResponseDTO:
        """Register a new user and return the created user profile.

        Raises
        ------
        DuplicateUserError
            If an account with *dto.email* already exists.
        """
        async with self._uow:
            existing = await self._uow.users.get_by_email(dto.email)
            if existing is not None:
                raise DuplicateUserError(dto.email)

            user = User.create(
                email=dto.email,
                hashed_password=hash_password(dto.password),
                first_name=dto.first_name,
                last_name=dto.last_name,
                role=dto.role,
            )
            await self._uow.users.add(user)
            await self._uow.commit()

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
