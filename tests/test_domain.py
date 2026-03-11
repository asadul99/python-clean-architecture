"""
Domain entity unit tests — equivalent to Order.Tests in C# xUnit.
Tests pure domain logic with NO infrastructure dependencies.

In .NET:
    [Fact]
    public void NewOrder_HasPendingStatus() {
        var order = new Order("John", "123 Main St");
        Assert.Equal(OrderStatus.Pending, order.Status);
    }
"""

import pytest
from domain.entities.order import Order, OrderStatus
from domain.exceptions import BusinessRuleViolationException


class TestOrder:
    """Like [Fact] / [Theory] tests in xUnit."""

    def test_new_order_has_pending_status(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        assert order.status == OrderStatus.PENDING

    def test_add_item_increases_total(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=2, unit_price=9.99)
        assert order.total == pytest.approx(19.98)

    def test_add_item_with_zero_quantity_raises(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        with pytest.raises(BusinessRuleViolationException, match="Quantity must be greater than zero"):
            order.add_item("Widget", quantity=0, unit_price=9.99)

    def test_add_item_with_negative_price_raises(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        with pytest.raises(BusinessRuleViolationException, match="Unit price cannot be negative"):
            order.add_item("Widget", quantity=1, unit_price=-5.0)

    def test_confirm_order_with_items_succeeds(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.confirm()
        assert order.status == OrderStatus.CONFIRMED

    def test_confirm_empty_order_raises(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        with pytest.raises(BusinessRuleViolationException, match="Cannot confirm an order with no items"):
            order.confirm()

    def test_cancel_pending_order_succeeds(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.cancel()
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_shipped_order_raises(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.confirm()
        order.ship()
        with pytest.raises(BusinessRuleViolationException, match="Cannot cancel order"):
            order.cancel()

    def test_multiple_items_total(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget A", quantity=2, unit_price=10.0)
        order.add_item("Widget B", quantity=3, unit_price=5.0)
        assert order.total == pytest.approx(35.0)


class TestOrderStateMachine:
    """Test the full order lifecycle — state machine transitions."""

    def test_full_lifecycle_pending_confirmed_shipped_delivered(self):
        """Happy path: Pending → Confirmed → Shipped → Delivered."""
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)

        assert order.status == OrderStatus.PENDING
        order.confirm()
        assert order.status == OrderStatus.CONFIRMED
        order.ship()
        assert order.status == OrderStatus.SHIPPED
        order.deliver()
        assert order.status == OrderStatus.DELIVERED

    def test_cannot_ship_pending_order(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        with pytest.raises(BusinessRuleViolationException, match="Must be confirmed first"):
            order.ship()

    def test_cannot_deliver_confirmed_order(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.confirm()
        with pytest.raises(BusinessRuleViolationException, match="Must be shipped first"):
            order.deliver()

    def test_cancel_confirmed_order_succeeds(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.confirm()
        order.cancel(reason="Changed my mind")
        assert order.status == OrderStatus.CANCELLED

    def test_cannot_cancel_delivered_order(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.confirm()
        order.ship()
        order.deliver()
        with pytest.raises(BusinessRuleViolationException, match="Cannot cancel order"):
            order.cancel()

    def test_cannot_confirm_cancelled_order(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.cancel()
        with pytest.raises(BusinessRuleViolationException, match="Cannot confirm order"):
            order.confirm()


class TestOrderDomainEvents:
    """Test that domain events are raised correctly."""

    def test_confirm_raises_order_confirmed_event(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.confirm()
        events = order.domain_events
        assert len(events) == 1
        assert events[0].__class__.__name__ == "OrderConfirmedEvent"

    def test_cancel_raises_order_cancelled_event(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.cancel(reason="Test")
        events = order.domain_events
        assert len(events) == 1
        assert events[0].__class__.__name__ == "OrderCancelledEvent"

    def test_mark_created_raises_order_created_event(self):
        order = Order(customer_name="John", shipping_address="123 Main St", id=42)
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.mark_created()
        events = order.domain_events
        assert len(events) == 1
        assert events[0].__class__.__name__ == "OrderCreatedEvent"
        assert events[0].order_id == 42

    def test_clear_domain_events(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.cancel()
        cleared = order.clear_domain_events()
        assert len(cleared) == 1
        assert len(order.domain_events) == 0


class TestOrderShippingAddress:
    """Test shipping address update rules."""

    def test_update_address_on_pending_order(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.update_shipping_address("456 Oak Ave")
        assert order.shipping_address == "456 Oak Ave"

    def test_update_address_on_confirmed_order(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.confirm()
        order.update_shipping_address("456 Oak Ave")
        assert order.shipping_address == "456 Oak Ave"

    def test_cannot_update_address_on_shipped_order(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("Widget", quantity=1, unit_price=10.0)
        order.confirm()
        order.ship()
        with pytest.raises(BusinessRuleViolationException, match="Cannot update shipping address"):
            order.update_shipping_address("456 Oak Ave")


class TestOrderItemCount:
    """Test computed properties."""

    def test_item_count(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        assert order.item_count == 0
        order.add_item("A", quantity=1, unit_price=1.0)
        order.add_item("B", quantity=1, unit_price=2.0)
        assert order.item_count == 2

    def test_remove_item(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        order.add_item("A", quantity=1, unit_price=1.0)
        order.add_item("B", quantity=1, unit_price=2.0)
        order.remove_item("A")
        assert order.item_count == 1
        assert order.total == pytest.approx(2.0)

    def test_remove_nonexistent_item_raises(self):
        order = Order(customer_name="John", shipping_address="123 Main St")
        with pytest.raises(BusinessRuleViolationException, match="not found in order"):
            order.remove_item("NonExistent")


