"""
DTOs — Pydantic models that act like your C# DTOs / AutoMapper destination types.

Pydantic replaces BOTH FluentValidation AND AutoMapper in Python:
  - Validation rules are declared as field constraints (like FluentValidation rules).
  - model_validate() / model_dump() handle mapping (like AutoMapper profiles).

.NET Equivalent:
    // FluentValidation
    public class CreateOrderCommandValidator : AbstractValidator<CreateOrderCommand> {
        RuleFor(x => x.CustomerName).NotEmpty().MinimumLength(2).MaximumLength(100);
    }

    // AutoMapper
    CreateMap<Order, OrderResponseDto>();
    CreateMap<OrderItem, OrderItemResponseDto>();
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ── Request DTOs (Command/Query payloads — validated on the way IN) ───────

class OrderItemCreateDto(BaseModel):
    """
    Equivalent to CreateOrderItemRequest in C#.

    FluentValidation equivalent:
        RuleFor(x => x.ProductName).NotEmpty().MaximumLength(200);
        RuleFor(x => x.Quantity).GreaterThan(0);
        RuleFor(x => x.UnitPrice).GreaterThanOrEqualTo(0);
    """
    product_name: str = Field(
        ..., min_length=1, max_length=200,
        description="Product name",
        json_schema_extra={"example": "Widget Pro"}
    )
    quantity: int = Field(
        ..., gt=0,
        description="Must be > 0",
        json_schema_extra={"example": 2}
    )
    unit_price: float = Field(
        ..., ge=0,
        description="Must be >= 0",
        json_schema_extra={"example": 29.99}
    )

    @field_validator("product_name")
    @classmethod
    def product_name_not_whitespace(cls, v: str) -> str:
        """Custom FluentValidation-style rule: name can't be just whitespace."""
        if not v.strip():
            raise ValueError("Product name cannot be only whitespace.")
        return v.strip()


class CreateOrderDto(BaseModel):
    """
    FluentValidation equivalent — rules are declared right on the fields.

    C# equivalent:
        public class CreateOrderCommandValidator : AbstractValidator<CreateOrderCommand> {
            RuleFor(x => x.CustomerName).NotEmpty().MinLength(2).MaxLength(100);
            RuleFor(x => x.ShippingAddress).NotEmpty().MinLength(5).MaxLength(300);
            RuleFor(x => x.Items).NotEmpty().WithMessage("At least one item required");
        }
    """
    customer_name: str = Field(
        ..., min_length=2, max_length=100,
        description="Customer full name",
        json_schema_extra={"example": "John Doe"}
    )
    shipping_address: str = Field(
        ..., min_length=5, max_length=300,
        description="Shipping address",
        json_schema_extra={"example": "123 Main St, Springfield, IL 62701"}
    )
    items: list[OrderItemCreateDto] = Field(
        ..., min_length=1,
        description="At least one item required"
    )

    @field_validator("customer_name")
    @classmethod
    def customer_name_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Customer name cannot be only whitespace.")
        return v.strip()

    @field_validator("shipping_address")
    @classmethod
    def shipping_address_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Shipping address cannot be only whitespace.")
        return v.strip()


class UpdateOrderDto(BaseModel):
    """
    Partial update DTO — like UpdateOrderCommand in C#.
    Optional fields — only provided fields are updated (PATCH semantics).
    """
    customer_name: str | None = Field(None, min_length=2, max_length=100)
    shipping_address: str | None = Field(None, min_length=5, max_length=300)


class OrderStatusAction(str, Enum):
    """
    Status transition actions — like an enum in your C# command.
    Instead of exposing raw status values, we expose actions:
      POST /api/orders/{id}/confirm
      POST /api/orders/{id}/cancel
    """
    CONFIRM = "confirm"
    SHIP = "ship"
    DELIVER = "deliver"
    CANCEL = "cancel"


class ChangeOrderStatusDto(BaseModel):
    """Request body for status transition."""
    action: OrderStatusAction = Field(..., description="The status transition to perform")
    reason: str = Field("", max_length=500, description="Reason (required for cancel)")


# ── Response DTOs (what the API returns — AutoMapper destination) ─────────

class OrderItemResponseDto(BaseModel):
    """
    AutoMapper destination for OrderItem → OrderItemResponseDto.
    ConfigDict(from_attributes=True) = like ForMember(dest => ..., opt => opt.MapFrom(src => ...))
    """
    model_config = ConfigDict(from_attributes=True)  # enables ORM-mode mapping like AutoMapper

    id: int
    product_name: str
    quantity: int
    unit_price: float
    line_total: float


class OrderResponseDto(BaseModel):
    """
    AutoMapper equivalent — `model_validate(order_entity)` maps Entity → DTO.
    ConfigDict(from_attributes=True) is the magic that makes this work,
    just like CreateMap<Order, OrderResponseDto>() in AutoMapper.

    Usage:
        # C#:  _mapper.Map<OrderResponseDto>(order);
        # Python: OrderResponseDto.model_validate(order)
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    shipping_address: str
    status: str
    total: float
    item_count: int
    items: list[OrderItemResponseDto]
    created_at: datetime
    updated_at: datetime | None = None


class PaginatedResponse(BaseModel):
    """Generic paginated response — like PagedResult<T> in C#."""
    items: list[OrderResponseDto]
    total_count: int
    page: int
    page_size: int
    total_pages: int


