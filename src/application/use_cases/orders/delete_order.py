"""
Delete Order command via MediatR pattern.

In C#:
    public record DeleteOrderCommand(int OrderId) : IRequest<Unit>;

    public class DeleteOrderCommandHandler : IRequestHandler<DeleteOrderCommand, Unit> {
        public async Task<Unit> Handle(DeleteOrderCommand request, CancellationToken ct) {
            var order = await _uow.Orders.GetByIdAsync(request.OrderId)
                ?? throw new NotFoundException(nameof(Order), request.OrderId);
            await _uow.Orders.DeleteAsync(request.OrderId);
            await _uow.CommitAsync();
            return Unit.Value;
        }
    }
"""

from dataclasses import dataclass

from mediatr import Mediator

from domain.exceptions import NotFoundException
from domain.interfaces.i_unit_of_work import IUnitOfWork

import structlog

logger = structlog.get_logger()


@dataclass
class DeleteOrderCommand:
    """Like IRequest<bool> in C#."""
    order_id: int


@Mediator.handler
class DeleteOrderCommandHandler:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, request: DeleteOrderCommand) -> bool:
        logger.info("Deleting order", order_id=request.order_id)
        async with self._uow:
            order = await self._uow.orders.get_by_id(request.order_id)
            if order is None:
                raise NotFoundException("Order", request.order_id)
            await self._uow.orders.delete(request.order_id)
            await self._uow.commit()
        logger.info("Order deleted", order_id=request.order_id)
        return True

