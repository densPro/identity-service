"""DTO for user login request."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserLoginDTO(BaseModel):
    """Payload for POST /api/v1/auth/login."""

    email: EmailStr
    password: str
