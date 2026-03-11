"""
OrderRepository — concrete implementation of IOrderRepository.
Equivalent to OrderRepository : IOrderRepository in your C# Infrastructure project.
Uses SQLAlchemy async sessions (like EF Core DbContext).
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.order import Order
from domain.interfaces.i_order_repository import IOrderRepository
from infrastructure.persistence.models import OrderModel
from infrastructure.repositories.mappers import order_model_to_entity, order_entity_to_model


class OrderRepository(IOrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self._session.get(OrderModel, order_id)
        if result is None:
            return None
        return order_model_to_entity(result)

    async def get_all(self) -> list[Order]:
        stmt = select(OrderModel).order_by(OrderModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [order_model_to_entity(m) for m in models]

    async def add(self, order: Order) -> Order:
        model = order_entity_to_model(order)
        self._session.add(model)
        await self._session.flush()  # generates the ID (like SaveChanges in EF)
        return order_model_to_entity(model)

    async def update(self, order: Order) -> Order:
        existing = await self._session.get(OrderModel, order.id)
        if existing is None:
            raise ValueError(f"Order {order.id} not found.")
        # Map all mutable fields from entity → ORM model
        existing.customer_name = order.customer_name
        existing.shipping_address = order.shipping_address
        existing.status = order.status
        existing.updated_at = order.updated_at or datetime.now(timezone.utc)
        await self._session.flush()
        return order_model_to_entity(existing)

    async def delete(self, order_id: int) -> None:
        model = await self._session.get(OrderModel, order_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

