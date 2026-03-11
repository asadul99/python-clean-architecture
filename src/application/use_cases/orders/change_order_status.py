"""
ChangeOrderStatus Command — state machine transitions via MediatR.

In C#:
    public record ChangeOrderStatusCommand(int OrderId, OrderStatusAction Action, string Reason)
        : IRequest<OrderResponseDto>;

    public class ChangeOrderStatusCommandHandler : IRequestHandler<ChangeOrderStatusCommand, OrderResponseDto> {
        public async Task<OrderResponseDto> Handle(ChangeOrderStatusCommand request, CancellationToken ct) {
            var order = await _uow.Orders.GetByIdAsync(request.OrderId)
                ?? throw new NotFoundException(nameof(Order), request.OrderId);
            switch (request.Action) {
                case OrderStatusAction.Confirm: order.Confirm(); break;
                case OrderStatusAction.Ship:    order.Ship();    break;
                case OrderStatusAction.Cancel:  order.Cancel(request.Reason); break;
            }
            await _uow.CommitAsync();
            return _mapper.Map<OrderResponseDto>(order);
        }
    }
"""

from dataclasses import dataclass

from mediatr import Mediator

from application.dtos.order_dtos import ChangeOrderStatusDto, OrderStatusAction, OrderResponseDto
from application.mappers import OrderMapper
from domain.exceptions import NotFoundException
from domain.interfaces.i_unit_of_work import IUnitOfWork

import structlog

logger = structlog.get_logger()


@dataclass
class ChangeOrderStatusCommand:
    """Like IRequest<OrderResponseDto> in C#."""
    order_id: int
    dto: ChangeOrderStatusDto


@Mediator.handler
class ChangeOrderStatusCommandHandler:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, request: ChangeOrderStatusCommand) -> OrderResponseDto:
        logger.info(
            "Changing order status",
            order_id=request.order_id,
            action=request.dto.action.value,
        )

        async with self._uow:
            order = await self._uow.orders.get_by_id(request.order_id)
            if order is None:
                raise NotFoundException("Order", request.order_id)

            # Domain entity enforces state machine rules (encapsulation)
            match request.dto.action:
                case OrderStatusAction.CONFIRM:
                    order.confirm()
                case OrderStatusAction.SHIP:
                    order.ship()
                case OrderStatusAction.DELIVER:
                    order.deliver()
                case OrderStatusAction.CANCEL:
                    order.cancel(reason=request.dto.reason)

            order = await self._uow.orders.update(order)
            await self._uow.commit()

        logger.info("Order status changed", order_id=order.id, new_status=order.status.value)
        return OrderMapper.to_response_dto(order)

