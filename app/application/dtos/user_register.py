"""DTO for user registration request."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.domain.enums.user_role import UserRole


class UserRegisterDTO(BaseModel):
    """Payload for POST /api/v1/auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.PATIENT
