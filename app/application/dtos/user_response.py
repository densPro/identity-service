"""DTO for user data responses."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.enums.user_role import UserRole
from app.domain.enums.user_status import UserStatus


class UserResponseDTO(BaseModel):
    """Serialized user data returned from the API."""

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
