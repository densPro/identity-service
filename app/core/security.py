"""Security utilities: password hashing and JWT management."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import settings
from app.domain.exceptions import TokenExpiredError, TokenInvalidError


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches the stored *hashed_password*."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# JWT management
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(UTC)


def create_access_token(
    subject: str,
    email: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    subject:
        The user's UUID as a string (stored in the ``sub`` claim).
    email:
        The user's email (stored in the ``email`` claim).
    role:
        The user's role string (stored in the ``role`` claim).
    expires_delta:
        Custom expiry window. Defaults to ``ACCESS_TOKEN_EXPIRE_MINUTES``.
    """
    expire = _utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": subject,
        "email": email,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": _utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT refresh token.

    Parameters
    ----------
    subject:
        The user's UUID as a string.
    expires_delta:
        Custom expiry window. Defaults to ``REFRESH_TOKEN_EXPIRE_DAYS``.
    """
    expire = _utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.refresh_token_expire_days)
    )
    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": expire,
        "iat": _utcnow(),
    }
    return jwt.encode(
        payload, settings.jwt_refresh_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_token(token: str, *, refresh: bool = False) -> dict:
    """Decode and validate a JWT token.

    Parameters
    ----------
    token:
        Raw JWT string.
    refresh:
        If ``True`` the token is validated against the refresh secret key,
        otherwise the access secret key is used.

    Raises
    ------
    TokenExpiredError
        When the token's ``exp`` claim is in the past.
    TokenInvalidError
        When the token cannot be decoded (bad signature, malformed, etc.).
    """
    secret = settings.jwt_refresh_secret_key if refresh else settings.jwt_secret_key
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError() from exc
    except jwt.PyJWTError as exc:
        raise TokenInvalidError(str(exc)) from exc
