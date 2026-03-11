"""
Unit of Work — equivalent to IUnitOfWork implementation in C#.
Wraps the database session and exposes repositories.
Commit/Rollback pattern just like in your .NET projects.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.interfaces.i_unit_of_work import IUnitOfWork
from infrastructure.repositories.order_repository import OrderRepository

import structlog

logger = structlog.get_logger()


class UnitOfWork(IUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> "UnitOfWork":
        self._session: AsyncSession = self._session_factory()
        self.orders = OrderRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
            logger.error("UoW rolling back due to exception", exc_type=str(exc_type))
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

