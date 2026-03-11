"""
CreateOrder Command — equivalent to IRequest<T> / IRequestHandler<T> in MediatR C#.

In C#:
    public record CreateOrderCommand(CreateOrderDto Dto) : IRequest<OrderResponseDto>;

    public class CreateOrderCommandHandler : IRequestHandler<CreateOrderCommand, OrderResponseDto> {
        private readonly IUnitOfWork _uow;
        private readonly IMapper _mapper;

        public async Task<OrderResponseDto> Handle(CreateOrderCommand request, CancellationToken ct) {
            var order = _mapper.Map<Order>(request.Dto);
            await _uow.Orders.AddAsync(order);
            await _uow.CommitAsync();
            return _mapper.Map<OrderResponseDto>(order);
        }
    }
"""

from dataclasses import dataclass

from mediatr import Mediator

from application.dtos.order_dtos import CreateOrderDto, OrderResponseDto
from application.mappers import OrderMapper
from domain.interfaces.i_unit_of_work import IUnitOfWork

import structlog

logger = structlog.get_logger()


# ── Command (like IRequest<OrderResponseDto> in C#) ──────────────────────

@dataclass
class CreateOrderCommand:
    """The command object — carries the validated DTO."""
    dto: CreateOrderDto


# ── Handler (like IRequestHandler<CreateOrderCommand, OrderResponseDto>) ─

@Mediator.handler
class CreateOrderCommandHandler:
    """
    Application service / use case.
    Equivalent to CreateOrderCommandHandler : IRequestHandler<...> in C#.
    The @Mediator.handler decorator registers this with the mediator pipeline.
    """

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, request: CreateOrderCommand) -> OrderResponseDto:
        logger.info("Creating order", customer=request.dto.customer_name)

        async with self._uow:
            # Map DTO → Domain Entity (like _mapper.Map<Order>(dto) in C#)
            order = OrderMapper.to_entity(request.dto)

            # Persist via repository (like await _uow.Orders.AddAsync(order))
            order = await self._uow.orders.add(order)

            # Raise domain event after persistence assigns ID
            order.mark_created()

            await self._uow.commit()

        logger.info("Order created", order_id=order.id, total=order.total)

        # Map Entity → Response DTO (like _mapper.Map<OrderResponseDto>(order))
        return OrderMapper.to_response_dto(order)

