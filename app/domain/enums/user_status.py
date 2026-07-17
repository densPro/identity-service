"""User account status enumeration."""

from enum import Enum


class UserStatus(str, Enum):
    """Lifecycle states of a user account."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
