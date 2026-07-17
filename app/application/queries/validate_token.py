"""Validate Token query."""

from __future__ import annotations

from app.application.dtos.token_response import TokenPayloadDTO
from app.core.security import decode_token


class ValidateTokenQuery:
    """Decode and validate an access JWT, returning its claims."""

    async def execute(self, token: str) -> TokenPayloadDTO:
        """Decode the access token and return its payload.

        Raises
        ------
        TokenExpiredError
            If the token's ``exp`` claim is in the past.
        TokenInvalidError
            If the token cannot be decoded or the signature is invalid.
        """
        payload = decode_token(token, refresh=False)
        return TokenPayloadDTO(
            sub=payload["sub"],
            email=payload["email"],
            role=payload["role"],
        )
