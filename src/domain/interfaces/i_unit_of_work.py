"""Unit of Work interface — equivalent to IUnitOfWork in C#."""

from abc import ABC, abstractmethod

from domain.interfaces.i_order_repository import IOrderRepository


class IUnitOfWork(ABC):
    orders: IOrderRepository

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...

    @abstractmethod
    async def __aenter__(self) -> "IUnitOfWork":
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

