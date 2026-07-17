"""Login User command."""

from __future__ import annotations

from app.application.dtos.token_response import TokenResponseDTO
from app.application.dtos.user_login import UserLoginDTO
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.domain.exceptions import InactiveUserError, InvalidCredentialsError


class LoginUserCommand:
    """Validates credentials and issues a JWT token pair."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: UserLoginDTO) -> TokenResponseDTO:
        """Authenticate a user and return an access + refresh token pair.

        Raises
        ------
        InvalidCredentialsError
            If no account exists for the email or the password is wrong.
        InactiveUserError
            If the account is suspended or inactive.
        """
        async with self._uow:
            user = await self._uow.users.get_by_email(dto.email)

        if user is None or not verify_password(dto.password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active():
            raise InactiveUserError()

        access_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            role=user.role.value,
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )
