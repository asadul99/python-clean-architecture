"""
Order entity — the Aggregate Root for the Order bounded context.

In .NET DDD:
    public class Order : AggregateRoot {
        private readonly List<OrderItem> _items = new();
        public IReadOnlyCollection<OrderItem> Items => _items.AsReadOnly();
        public void AddItem(...) { ... AddDomainEvent(new OrderCreatedEvent()); }
    }
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from domain.entities.base_entity import BaseEntity
from domain.entities.order_item import OrderItem
from domain.events import OrderCreatedEvent, OrderConfirmedEvent, OrderCancelledEvent
from domain.exceptions import BusinessRuleViolationException


class OrderStatus(str, Enum):
    """Order lifecycle states — like an enum in your C# Domain project."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(BaseEntity):
    """
    Aggregate Root.
    Equivalent to an Order entity in your C# Domain project.
    Business rules live HERE, not in services.

    Key OOP concepts for .NET devs:
    - Encapsulation: status transitions are guarded by methods
    - Domain Events: side-effects are decoupled via events
    - Rich Domain Model: logic lives on the entity, not in anaemic services
    """

    def __init__(
        self,
        customer_name: str,
        shipping_address: str,
        id: int | None = None,
    ) -> None:
        super().__init__(id)
        self.customer_name = customer_name
        self.shipping_address = shipping_address
        self.status: OrderStatus = OrderStatus.PENDING
        self.items: list[OrderItem] = []

    # ── Domain behaviour (encapsulated business rules) ────────────

    def add_item(self, product_name: str, quantity: int, unit_price: float) -> None:
        """
        Add a line item to the order.
        Equivalent to Order.AddItem() in C# with guard clauses.
        """
        if quantity <= 0:
            raise BusinessRuleViolationException("Quantity must be greater than zero.")
        if unit_price < 0:
            raise BusinessRuleViolationException("Unit price cannot be negative.")
        self.items.append(
            OrderItem(product_name=product_name, quantity=quantity, unit_price=unit_price)
        )

    def remove_item(self, product_name: str) -> None:
        """Remove an item by product name."""
        item = next((i for i in self.items if i.product_name == product_name), None)
        if item is None:
            raise BusinessRuleViolationException(f"Item '{product_name}' not found in order.")
        self.items.remove(item)

    def confirm(self) -> None:
        """
        Transition to Confirmed — like Order.Confirm() in C# with state machine.
        Raises a domain event that other handlers can subscribe to.
        """
        if self.status != OrderStatus.PENDING:
            raise BusinessRuleViolationException(
                f"Cannot confirm order in '{self.status.value}' status."
            )
        if not self.items:
            raise BusinessRuleViolationException("Cannot confirm an order with no items.")
        self.status = OrderStatus.CONFIRMED
        self.updated_at = datetime.now(timezone.utc)
        self.add_domain_event(OrderConfirmedEvent(order_id=self.id or 0))

    def ship(self) -> None:
        """Transition to Shipped."""
        if self.status != OrderStatus.CONFIRMED:
            raise BusinessRuleViolationException(
                f"Cannot ship order in '{self.status.value}' status. Must be confirmed first."
            )
        self.status = OrderStatus.SHIPPED
        self.updated_at = datetime.now(timezone.utc)

    def deliver(self) -> None:
        """Transition to Delivered."""
        if self.status != OrderStatus.SHIPPED:
            raise BusinessRuleViolationException(
                f"Cannot deliver order in '{self.status.value}' status. Must be shipped first."
            )
        self.status = OrderStatus.DELIVERED
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self, reason: str = "") -> None:
        """
        Cancel the order — guarded by state machine rules.
        Cannot cancel if already shipped or delivered.
        """
        if self.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            raise BusinessRuleViolationException(
                f"Cannot cancel order in '{self.status.value}' status."
            )
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)
        self.add_domain_event(OrderCancelledEvent(order_id=self.id or 0, reason=reason))

    def update_shipping_address(self, new_address: str) -> None:
        """Can only update address before shipping."""
        if self.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            raise BusinessRuleViolationException(
                "Cannot update shipping address after order has been shipped."
            )
        self.shipping_address = new_address
        self.updated_at = datetime.now(timezone.utc)

    def mark_created(self) -> None:
        """
        Called after persistence assigns an ID.
        Raises OrderCreatedEvent so other handlers can react.
        """
        self.add_domain_event(
            OrderCreatedEvent(
                order_id=self.id or 0,
                customer_name=self.customer_name,
                total=self.total,
            )
        )

    @property
    def total(self) -> float:
        """Computed property — like a C# calculated property."""
        return sum(item.line_total for item in self.items)

    @property
    def item_count(self) -> int:
        return len(self.items)

