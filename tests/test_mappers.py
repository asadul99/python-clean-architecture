"""
Mapper unit tests — equivalent to AutoMapper Profile tests in C#.
Tests that Pydantic model_validate() correctly maps entities to DTOs.

In .NET:
    [Fact]
    public void Should_Map_Order_To_OrderResponseDto() {
        var order = new Order("John", "123 Main St");
        order.AddItem("Widget", 2, 9.99m);
        var dto = _mapper.Map<OrderResponseDto>(order);
        Assert.Equal("John", dto.CustomerName);
    }
"""

import pytest
from domain.entities.order import Order
from application.dtos.order_dtos import CreateOrderDto, OrderItemCreateDto
from application.mappers import OrderMapper


class TestOrderMapper:
    """Like testing AutoMapper profiles in C#."""

    def test_entity_to_response_dto(self):
        """Test Entity → Response DTO mapping (AutoMapper.Map<OrderResponseDto>)."""
        order = Order(customer_name="John Doe", shipping_address="123 Main St", id=1)
        order.add_item("Widget", quantity=2, unit_price=9.99)
        order.add_item("Gadget", quantity=1, unit_price=14.99)
        # Simulate DB-assigned IDs (normally set by ORM after flush)
        order.items[0].id = 10
        order.items[1].id = 11

        dto = OrderMapper.to_response_dto(order)

        assert dto.id == 1
        assert dto.customer_name == "John Doe"
        assert dto.shipping_address == "123 Main St"
        assert dto.status == "pending"
        assert dto.total == pytest.approx(34.97)
        assert dto.item_count == 2
        assert len(dto.items) == 2
        assert dto.items[0].product_name == "Widget"
        assert dto.items[0].line_total == pytest.approx(19.98)

    def test_entity_list_to_response_dto_list(self):
        """Test List<Entity> → List<DTO> mapping."""
        orders = [
            Order(customer_name="John", shipping_address="123 Main", id=1),
            Order(customer_name="Jane", shipping_address="456 Oak", id=2),
        ]
        orders[0].add_item("A", quantity=1, unit_price=10.0)
        orders[0].items[0].id = 10
        orders[1].add_item("B", quantity=2, unit_price=5.0)
        orders[1].items[0].id = 20

        dtos = OrderMapper.to_response_dto_list(orders)

        assert len(dtos) == 2
        assert dtos[0].customer_name == "John"
        assert dtos[1].customer_name == "Jane"

    def test_create_dto_to_entity(self):
        """Test CreateOrderDto → Entity mapping (AutoMapper reverse map)."""
        dto = CreateOrderDto(
            customer_name="John Doe",
            shipping_address="123 Main St, City",
            items=[
                OrderItemCreateDto(product_name="Widget", quantity=2, unit_price=9.99),
                OrderItemCreateDto(product_name="Gadget", quantity=1, unit_price=14.99),
            ],
        )

        order = OrderMapper.to_entity(dto)

        assert order.customer_name == "John Doe"
        assert order.shipping_address == "123 Main St, City"
        assert len(order.items) == 2
        assert order.items[0].product_name == "Widget"
        assert order.items[0].quantity == 2
        assert order.total == pytest.approx(34.97)

    def test_empty_order_maps_correctly(self):
        """Edge case: order with no items."""
        order = Order(customer_name="Test", shipping_address="Test Addr", id=99)
        dto = OrderMapper.to_response_dto(order)
        assert dto.total == 0.0
        assert dto.item_count == 0
        assert dto.items == []


