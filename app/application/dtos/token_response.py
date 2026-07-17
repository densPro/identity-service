"""DTOs for token responses and refresh requests."""

from __future__ import annotations

from pydantic import BaseModel


class TokenResponseDTO(BaseModel):
    """Returned after successful login or token refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenDTO(BaseModel):
    """Payload for POST /api/v1/auth/refresh."""

    refresh_token: str


class TokenValidateDTO(BaseModel):
    """Payload for POST /api/v1/auth/validate."""

    token: str


class TokenPayloadDTO(BaseModel):
    """Decoded token claims returned by the validate endpoint."""

    sub: str
    email: str
    role: str
