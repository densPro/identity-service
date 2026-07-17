"""Refresh Token command."""

from __future__ import annotations

import uuid

from app.application.dtos.token_response import TokenResponseDTO
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.domain.exceptions import InactiveUserError, UserNotFoundError


class RefreshTokenCommand:
    """Issues a new access token (and rotated refresh token) from a valid refresh token."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, refresh_token: str) -> TokenResponseDTO:
        """Rotate the refresh token and issue a new access token.

        Raises
        ------
        TokenExpiredError / TokenInvalidError
            Propagated from ``decode_token`` when the token is bad.
        UserNotFoundError
            If the subject encoded in the token no longer exists.
        InactiveUserError
            If the account has been suspended since the token was issued.
        """
        payload = decode_token(refresh_token, refresh=True)
        user_id = uuid.UUID(payload["sub"])

        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError(str(user_id))

        if not user.is_active():
            raise InactiveUserError()

        new_access_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            role=user.role.value,
        )
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponseDTO(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )
