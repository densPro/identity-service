"""SQLAlchemy Unit of Work implementation."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.repositories.user_repository import UserRepository


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """Concrete Unit of Work backed by an async SQLAlchemy session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.users = UserRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        await self._session.close()  # type: ignore[union-attr]

    async def commit(self) -> None:
        """Flush and commit the current transaction."""
        await self._session.commit()  # type: ignore[union-attr]

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self._session.rollback()  # type: ignore[union-attr]
