"""
Domain Events — equivalent to MediatR INotification / INotificationHandler in C#.

In .NET Clean Architecture you'd have:
    public class OrderCreatedEvent : INotification { ... }
    public class OrderCreatedEventHandler : INotificationHandler<OrderCreatedEvent> { ... }

Domain events decouple side-effects from the main use case.
The entity records events; the handler publishes them after commit.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DomainEvent:
    """Base class for all domain events — like INotification in MediatR."""
    occurred_on: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class OrderCreatedEvent(DomainEvent):
    """Raised when a new order is successfully created."""
    order_id: int = 0
    customer_name: str = ""
    total: float = 0.0


@dataclass
class OrderConfirmedEvent(DomainEvent):
    """Raised when an order transitions to Confirmed status."""
    order_id: int = 0


@dataclass
class OrderCancelledEvent(DomainEvent):
    """Raised when an order is cancelled."""
    order_id: int = 0
    reason: str = ""


@dataclass
class OrderDeletedEvent(DomainEvent):
    """Raised when an order is deleted."""
    order_id: int = 0


class HasDomainEvents:
    """
    Mixin for entities that raise domain events.
    Equivalent to Entity base class with List<INotification> DomainEvents in C#.
    """

    def __init__(self) -> None:
        self._domain_events: list[DomainEvent] = []

    @property
    def domain_events(self) -> list[DomainEvent]:
        return list(self._domain_events)

    def add_domain_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def clear_domain_events(self) -> list[DomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

