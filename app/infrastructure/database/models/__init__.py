"""Models package — import all models so Alembic can detect them."""

from app.infrastructure.database.models.user_model import UserModel  # noqa: F401

__all__ = ["UserModel"]
