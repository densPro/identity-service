"""Domain-specific exceptions for the identity service."""


class IdentityError(Exception):
    """Base exception for all identity-service domain errors."""

    def __init__(self, message: str = "An identity service error occurred.") -> None:
        self.message = message
        super().__init__(self.message)


class UserNotFoundError(IdentityError):
    """Raised when a user cannot be found by ID or email."""

    def __init__(self, identifier: str) -> None:
        super().__init__(f"User not found: {identifier}")
        self.identifier = identifier


class DuplicateUserError(IdentityError):
    """Raised when attempting to register an email that already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(f"A user with email '{email}' already exists.")
        self.email = email


class InvalidCredentialsError(IdentityError):
    """Raised when email/password combination is invalid."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password.")


class TokenExpiredError(IdentityError):
    """Raised when a JWT token has expired."""

    def __init__(self) -> None:
        super().__init__("Token has expired.")


class TokenInvalidError(IdentityError):
    """Raised when a JWT token cannot be decoded or has an invalid signature."""

    def __init__(self, detail: str = "Token is invalid.") -> None:
        super().__init__(f"Token is invalid: {detail}")
        self.detail = detail


class InactiveUserError(IdentityError):
    """Raised when a suspended or inactive user attempts to authenticate."""

    def __init__(self) -> None:
        super().__init__("User account is inactive or suspended.")
