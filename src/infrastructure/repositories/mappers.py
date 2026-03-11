"""
Mapper — converts between Domain Entities and ORM Models.
This is the equivalent of AutoMapper profiles that map Entity ↔ Persistence Model.
In C# Clean Architecture you'd have IMapper.Map<Order>(orderModel).
"""

from domain.entities.order import Order, OrderStatus
from domain.entities.order_item import OrderItem
from infrastructure.persistence.models import OrderModel, OrderItemModel


def order_model_to_entity(model: OrderModel) -> Order:
    """ORM Model → Domain Entity (like AutoMapper reverse map)."""
    order = Order(
        customer_name=model.customer_name,
        shipping_address=model.shipping_address,
        id=model.id,
    )
    order.status = OrderStatus(model.status) if isinstance(model.status, str) else model.status
    order.created_at = model.created_at
    order.updated_at = model.updated_at
    order.items = [
        _order_item_model_to_entity(item) for item in model.items
    ]
    return order


def _order_item_model_to_entity(model: OrderItemModel) -> OrderItem:
    return OrderItem(
        product_name=model.product_name,
        quantity=model.quantity,
        unit_price=model.unit_price,
        id=model.id,
    )


def order_entity_to_model(entity: Order) -> OrderModel:
    """Domain Entity → ORM Model (like AutoMapper CreateMap<Order, OrderModel>)."""
    model = OrderModel(
        customer_name=entity.customer_name,
        shipping_address=entity.shipping_address,
        status=entity.status,
    )
    model.items = [
        OrderItemModel(
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        for item in entity.items
    ]
    return model

