"""Abstract Unit of Work interface (port)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from app.application.interfaces.user_repository import IUserRepository


class IUnitOfWork(ABC):
    """Port defining the contract for a transactional unit of work.

    Usage::

        async with uow:
            user = await uow.users.get_by_email(email)
            await uow.commit()
    """

    users: IUserRepository

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back the current transaction."""
        ...

    @abstractmethod
    async def __aenter__(self) -> "IUnitOfWork":
        ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...
