"""
Queries — read-only use cases using MediatR pattern.

In C#:
    public record GetOrderByIdQuery(int OrderId) : IRequest<OrderResponseDto>;

    public class GetOrderByIdQueryHandler : IRequestHandler<GetOrderByIdQuery, OrderResponseDto> {
        public async Task<OrderResponseDto> Handle(GetOrderByIdQuery request, CancellationToken ct) {
            var order = await _uow.Orders.GetByIdAsync(request.OrderId)
                ?? throw new NotFoundException(nameof(Order), request.OrderId);
            return _mapper.Map<OrderResponseDto>(order);
        }
    }
"""

from dataclasses import dataclass

from mediatr import Mediator

from application.dtos.order_dtos import OrderResponseDto
from application.mappers import OrderMapper
from domain.exceptions import NotFoundException
from domain.interfaces.i_unit_of_work import IUnitOfWork

import structlog

logger = structlog.get_logger()


# ── Get Order By Id ──────────────────────────────────────────────────────

@dataclass
class GetOrderByIdQuery:
    """Like IRequest<OrderResponseDto> in C#."""
    order_id: int


@Mediator.handler
class GetOrderByIdQueryHandler:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, request: GetOrderByIdQuery) -> OrderResponseDto:
        logger.info("Fetching order", order_id=request.order_id)
        async with self._uow:
            order = await self._uow.orders.get_by_id(request.order_id)
            if order is None:
                raise NotFoundException("Order", request.order_id)
            return OrderMapper.to_response_dto(order)


# ── Get All Orders ───────────────────────────────────────────────────────

@dataclass
class GetAllOrdersQuery:
    """Like IRequest<List<OrderResponseDto>> in C#."""
    pass


@Mediator.handler
class GetAllOrdersQueryHandler:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, request: GetAllOrdersQuery) -> list[OrderResponseDto]:
        logger.info("Fetching all orders")
        async with self._uow:
            orders = await self._uow.orders.get_all()
            return OrderMapper.to_response_dto_list(orders)
