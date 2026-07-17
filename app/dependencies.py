"""FastAPI dependency injection wiring."""

from __future__ import annotations

from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def get_unit_of_work() -> IUnitOfWork:
    """Provide a Unit of Work instance for each request.

    This is used as a FastAPI ``Depends()`` dependency.
    """
    return SqlAlchemyUnitOfWork(async_session_factory)
