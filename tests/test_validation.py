"""
DTO / Pydantic validation tests — equivalent to FluentValidation unit tests.
Tests that Pydantic enforces the same rules FluentValidation would in C#.
"""

import pytest
from pydantic import ValidationError

from application.dtos.order_dtos import CreateOrderDto, OrderItemCreateDto


class TestCreateOrderDtoValidation:
    """Like testing CreateOrderCommandValidator in C#."""

    def test_valid_dto_passes(self):
        dto = CreateOrderDto(
            customer_name="John Doe",
            shipping_address="123 Main St, City",
            items=[OrderItemCreateDto(product_name="Widget", quantity=2, unit_price=9.99)],
        )
        assert dto.customer_name == "John Doe"

    def test_empty_customer_name_fails(self):
        with pytest.raises(ValidationError) as exc_info:
            CreateOrderDto(
                customer_name="",
                shipping_address="123 Main St, City",
                items=[OrderItemCreateDto(product_name="Widget", quantity=2, unit_price=9.99)],
            )
        assert "customer_name" in str(exc_info.value)

    def test_short_customer_name_fails(self):
        with pytest.raises(ValidationError):
            CreateOrderDto(
                customer_name="J",  # min_length=2
                shipping_address="123 Main St, City",
                items=[OrderItemCreateDto(product_name="Widget", quantity=2, unit_price=9.99)],
            )

    def test_empty_items_fails(self):
        with pytest.raises(ValidationError):
            CreateOrderDto(
                customer_name="John Doe",
                shipping_address="123 Main St, City",
                items=[],  # min_length=1
            )

    def test_zero_quantity_fails(self):
        with pytest.raises(ValidationError):
            OrderItemCreateDto(product_name="Widget", quantity=0, unit_price=9.99)

    def test_negative_price_fails(self):
        with pytest.raises(ValidationError):
            OrderItemCreateDto(product_name="Widget", quantity=1, unit_price=-1.0)

    def test_short_address_fails(self):
        with pytest.raises(ValidationError):
            CreateOrderDto(
                customer_name="John Doe",
                shipping_address="123",  # min_length=5
                items=[OrderItemCreateDto(product_name="Widget", quantity=1, unit_price=9.99)],
            )

