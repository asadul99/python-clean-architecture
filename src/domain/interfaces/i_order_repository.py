"""
Repository interface — equivalent to IOrderRepository in C#.
Domain layer defines the contract; Infrastructure layer provides the implementation.
This is the Dependency Inversion Principle in action.
"""

from abc import ABC, abstractmethod

from domain.entities.order import Order


class IOrderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, order_id: int) -> Order | None:
        ...

    @abstractmethod
    async def get_all(self) -> list[Order]:
        ...

    @abstractmethod
    async def add(self, order: Order) -> Order:
        ...

    @abstractmethod
    async def update(self, order: Order) -> Order:
        ...

    @abstractmethod
    async def delete(self, order_id: int) -> None:
        ...

