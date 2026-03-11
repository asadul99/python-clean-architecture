"""
MediatR Pipeline Behaviors — equivalent to IPipelineBehavior<TRequest, TResponse> in C#.

In .NET MediatR:
    public class LoggingBehavior<TReq, TRes> : IPipelineBehavior<TReq, TRes> {
        public async Task<TRes> Handle(TReq request, RequestHandlerDelegate<TRes> next, ...) {
            _logger.LogInformation("Handling {RequestName}", typeof(TReq).Name);
            var response = await next();
            _logger.LogInformation("Handled {RequestName}", typeof(TReq).Name);
            return response;
        }
    }

In Python we implement this as wrapper functions that the Mediator calls
before/after the actual handler.
"""

import time
from typing import Any

import structlog

logger = structlog.get_logger()


class LoggingBehavior:
    """
    Cross-cutting logging — like LoggingBehavior<TRequest, TResponse> in C#.
    Logs every MediatR request with timing info (like Serilog + MediatR pipeline).
    """

    async def handle(self, request: Any, next_handler) -> Any:
        request_name = type(request).__name__
        logger.info(
            "MediatR Pipeline: Handling request",
            request_type=request_name,
            request_data=str(request),
        )

        start_time = time.perf_counter()
        try:
            response = await next_handler()
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "MediatR Pipeline: Request handled successfully",
                request_type=request_name,
                elapsed_ms=round(elapsed_ms, 2),
            )
            return response
        except Exception as ex:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "MediatR Pipeline: Request failed",
                request_type=request_name,
                elapsed_ms=round(elapsed_ms, 2),
                error=str(ex),
                error_type=type(ex).__name__,
            )
            raise


class PerformanceBehavior:
    """
    Performance monitoring — like PerformanceBehavior in C# MediatR pipeline.
    Warns if a handler takes longer than the threshold.
    """

    SLOW_THRESHOLD_MS = 500

    async def handle(self, request: Any, next_handler) -> Any:
        start_time = time.perf_counter()
        response = await next_handler()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if elapsed_ms > self.SLOW_THRESHOLD_MS:
            logger.warning(
                "SLOW HANDLER DETECTED",
                request_type=type(request).__name__,
                elapsed_ms=round(elapsed_ms, 2),
                threshold_ms=self.SLOW_THRESHOLD_MS,
            )
        return response

