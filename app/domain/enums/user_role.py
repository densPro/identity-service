"""User role enumeration."""

from enum import Enum


class UserRole(str, Enum):
    """Roles available in the Chirimoya platform."""

    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"
    STAFF = "staff"
