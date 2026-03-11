"""
UpdateOrder Command — equivalent to IRequestHandler<UpdateOrderCommand, OrderResponseDto> in C#.

In C#:
    public record UpdateOrderCommand(int OrderId, UpdateOrderDto Dto) : IRequest<OrderResponseDto>;

    public class UpdateOrderCommandHandler : IRequestHandler<UpdateOrderCommand, OrderResponseDto> {
        public async Task<OrderResponseDto> Handle(UpdateOrderCommand request, CancellationToken ct) {
            var order = await _uow.Orders.GetByIdAsync(request.OrderId)
                ?? throw new NotFoundException(nameof(Order), request.OrderId);
            if (request.Dto.CustomerName != null) order.CustomerName = request.Dto.CustomerName;
            if (request.Dto.ShippingAddress != null) order.UpdateShippingAddress(request.Dto.ShippingAddress);
            await _uow.CommitAsync();
            return _mapper.Map<OrderResponseDto>(order);
        }
    }
"""

from dataclasses import dataclass

from mediatr import Mediator

from application.dtos.order_dtos import UpdateOrderDto, OrderResponseDto
from application.mappers import OrderMapper
from domain.exceptions import NotFoundException
from domain.interfaces.i_unit_of_work import IUnitOfWork

import structlog

logger = structlog.get_logger()


@dataclass
class UpdateOrderCommand:
    """Like IRequest<OrderResponseDto> in C#."""
    order_id: int
    dto: UpdateOrderDto


@Mediator.handler
class UpdateOrderCommandHandler:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, request: UpdateOrderCommand) -> OrderResponseDto:
        logger.info("Updating order", order_id=request.order_id)

        async with self._uow:
            order = await self._uow.orders.get_by_id(request.order_id)
            if order is None:
                raise NotFoundException("Order", request.order_id)

            # Apply only provided fields (partial update / PATCH semantics)
            if request.dto.customer_name is not None:
                order.customer_name = request.dto.customer_name

            if request.dto.shipping_address is not None:
                order.update_shipping_address(request.dto.shipping_address)

            order = await self._uow.orders.update(order)
            await self._uow.commit()

        logger.info("Order updated", order_id=order.id)
        return OrderMapper.to_response_dto(order)

