"""
Order API routes — equivalent to OrdersController : ControllerBase in C#.

In .NET:
    [ApiController]
    [Route("api/[controller]")]
    public class OrdersController : ControllerBase {
        private readonly IMediator _mediator;

        public OrdersController(IMediator mediator) => _mediator = mediator;

        [HttpPost] public async Task<ActionResult<OrderDto>> Create(CreateOrderCommand cmd)
            => CreatedAtAction(nameof(Get), new { id = result.Id }, result);

        [HttpGet("{id}")] public async Task<ActionResult<OrderDto>> Get(int id)
            => Ok(await _mediator.Send(new GetOrderByIdQuery(id)));
    }

In Python/FastAPI:
    @router.post("/") async def create_order(dto, request): ...
    @router.get("/{order_id}") async def get_order(order_id, request): ...
"""

from fastapi import APIRouter, Request, status

from mediatr import Mediator

from application.dtos.order_dtos import (
    CreateOrderDto,
    UpdateOrderDto,
    ChangeOrderStatusDto,
    OrderResponseDto,
)
from application.use_cases.orders.create_order import CreateOrderCommand
from application.use_cases.orders.get_orders import GetOrderByIdQuery, GetAllOrdersQuery
from application.use_cases.orders.delete_order import DeleteOrderCommand
from application.use_cases.orders.update_order import UpdateOrderCommand
from application.use_cases.orders.change_order_status import ChangeOrderStatusCommand

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/orders", tags=["Orders"])


def _get_mediator(request: Request) -> Mediator:
    """
    Resolve the Mediator from the app state (set during startup in main.py).
    Like constructor injection of IMediator in C# controllers.
    """
    return request.app.state.mediator


# ── POST /api/orders ─────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=OrderResponseDto,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Creates a new order with line items. Pydantic validates the request (FluentValidation equivalent).",
)
async def create_order(
    dto: CreateOrderDto,  # Pydantic validates this automatically (FluentValidation equivalent)
    request: Request,
) -> OrderResponseDto:
    """
    Equivalent to:
        [HttpPost]
        public async Task<ActionResult<OrderResponseDto>> Create(
            [FromBody] CreateOrderDto dto)
            => CreatedAtAction(nameof(Get), new { id = result.Id },
                await _mediator.Send(new CreateOrderCommand(dto)));
    """
    mediator = _get_mediator(request)
    logger.info("POST /api/orders", customer=dto.customer_name)
    return await mediator.send_async(CreateOrderCommand(dto=dto))


# ── GET /api/orders ──────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[OrderResponseDto],
    summary="Get all orders",
    description="Returns all orders with their line items.",
)
async def get_all_orders(request: Request) -> list[OrderResponseDto]:
    """
    Equivalent to:
        [HttpGet]
        public async Task<ActionResult<List<OrderResponseDto>>> GetAll()
            => Ok(await _mediator.Send(new GetAllOrdersQuery()));
    """
    mediator = _get_mediator(request)
    return await mediator.send_async(GetAllOrdersQuery())


# ── GET /api/orders/{order_id} ───────────────────────────────────────────

@router.get(
    "/{order_id}",
    response_model=OrderResponseDto,
    summary="Get order by ID",
    description="Returns a single order. Raises 404 if not found.",
)
async def get_order(order_id: int, request: Request) -> OrderResponseDto:
    """
    Equivalent to:
        [HttpGet("{id}")]
        public async Task<ActionResult<OrderResponseDto>> Get(int id)
            => Ok(await _mediator.Send(new GetOrderByIdQuery(id)));

    Note: NotFoundException is thrown by the handler and caught by exception middleware.
    No need for manual 404 checks here — just like C# with global exception handling.
    """
    mediator = _get_mediator(request)
    return await mediator.send_async(GetOrderByIdQuery(order_id=order_id))


# ── PUT /api/orders/{order_id} ───────────────────────────────────────────

@router.put(
    "/{order_id}",
    response_model=OrderResponseDto,
    summary="Update an order",
    description="Updates customer name and/or shipping address. Only provided fields are updated.",
)
async def update_order(
    order_id: int,
    dto: UpdateOrderDto,
    request: Request,
) -> OrderResponseDto:
    """
    Equivalent to:
        [HttpPut("{id}")]
        public async Task<ActionResult<OrderResponseDto>> Update(int id, UpdateOrderDto dto)
            => Ok(await _mediator.Send(new UpdateOrderCommand(id, dto)));
    """
    mediator = _get_mediator(request)
    logger.info("PUT /api/orders", order_id=order_id)
    return await mediator.send_async(UpdateOrderCommand(order_id=order_id, dto=dto))


# ── POST /api/orders/{order_id}/status ───────────────────────────────────

@router.post(
    "/{order_id}/status",
    response_model=OrderResponseDto,
    summary="Change order status",
    description="Performs a status transition (confirm, ship, deliver, cancel). "
                "Domain entity enforces valid transitions.",
)
async def change_order_status(
    order_id: int,
    dto: ChangeOrderStatusDto,
    request: Request,
) -> OrderResponseDto:
    """
    Equivalent to:
        [HttpPost("{id}/status")]
        public async Task<ActionResult<OrderResponseDto>> ChangeStatus(
            int id, ChangeOrderStatusDto dto)
            => Ok(await _mediator.Send(new ChangeOrderStatusCommand(id, dto)));

    The domain entity (Order.Confirm(), Order.Ship(), etc.) enforces the state machine.
    BusinessRuleViolationException is thrown for invalid transitions → HTTP 422.
    """
    mediator = _get_mediator(request)
    logger.info("POST /api/orders/status", order_id=order_id, action=dto.action.value)
    return await mediator.send_async(ChangeOrderStatusCommand(order_id=order_id, dto=dto))


# ── DELETE /api/orders/{order_id} ────────────────────────────────────────

@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an order",
    description="Permanently deletes an order. Returns 404 if not found.",
)
async def delete_order(order_id: int, request: Request) -> None:
    """
    Equivalent to:
        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(int id) {
            await _mediator.Send(new DeleteOrderCommand(id));
            return NoContent();
        }
    """
    mediator = _get_mediator(request)
    await mediator.send_async(DeleteOrderCommand(order_id=order_id))
