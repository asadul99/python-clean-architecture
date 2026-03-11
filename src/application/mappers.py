"""
Application Mapper Service — equivalent to AutoMapper IMapper in C#.

In .NET:
    public class MappingProfile : Profile {
        CreateMap<Order, OrderResponseDto>();
        CreateMap<CreateOrderDto, Order>();
    }

    // Usage:
    var dto = _mapper.Map<OrderResponseDto>(order);

In Python, Pydantic's model_validate() does the heavy lifting, but we wrap it
in a mapper service for consistency and to centralize mapping logic.
"""

from domain.entities.order import Order
from application.dtos.order_dtos import (
    CreateOrderDto,
    OrderResponseDto,
)


class OrderMapper:
    """
    Centralized mapping — like an AutoMapper Profile for Orders.

    In C# you'd register:
        services.AddAutoMapper(typeof(MappingProfile));

    Then inject:
        private readonly IMapper _mapper;
        var dto = _mapper.Map<OrderResponseDto>(order);

    In Python:
        dto = OrderMapper.to_response_dto(order)
        entity = OrderMapper.to_entity(create_dto)
    """

    @staticmethod
    def to_response_dto(order: Order) -> OrderResponseDto:
        """
        Entity → Response DTO.
        Equivalent to: _mapper.Map<OrderResponseDto>(order)
        """
        return OrderResponseDto.model_validate(order)

    @staticmethod
    def to_response_dto_list(orders: list[Order]) -> list[OrderResponseDto]:
        """
        List<Entity> → List<ResponseDTO>.
        Equivalent to: _mapper.Map<List<OrderResponseDto>>(orders)
        """
        return [OrderResponseDto.model_validate(o) for o in orders]

    @staticmethod
    def to_entity(dto: CreateOrderDto) -> Order:
        """
        CreateOrderDto → Domain Entity.
        Equivalent to: _mapper.Map<Order>(createOrderDto)

        NOTE: In DDD, we use the entity's own methods (add_item) rather than
        blindly mapping all fields. This preserves invariants.
        """
        order = Order(
            customer_name=dto.customer_name,
            shipping_address=dto.shipping_address,
        )
        for item in dto.items:
            order.add_item(
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        return order


