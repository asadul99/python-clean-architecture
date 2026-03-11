"""
Correlation ID Middleware — equivalent to app.UseCorrelationId() in C#.

In .NET you'd use:
    builder.Services.AddCorrelationIdForwarding();
    app.UseCorrelationId();

This generates/propagates a correlation ID for every request,
attaches it to structlog context, and returns it in the response header.
Invaluable for distributed tracing across microservices.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

import structlog


CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Equivalent to CorrelationIdMiddleware in ASP.NET Core.

    For each request:
    1. Read X-Correlation-ID header (if present — forwarded from upstream service)
    2. Otherwise generate a new UUID
    3. Bind it to structlog context (appears in all log messages for this request)
    4. Return it in the response header
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Read or generate correlation ID
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())

        # Bind to structlog context — like Serilog PushProperty("CorrelationId", ...)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Store on request state for easy access in route handlers
        request.state.correlation_id = correlation_id

        # Process the request
        response = await call_next(request)

        # Echo back in response header
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response

