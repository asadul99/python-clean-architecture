"""
Exception handling middleware — equivalent to app.UseExceptionHandler() in C#.
Catches unhandled exceptions and returns consistent ProblemDetails-style JSON.

In .NET you'd configure:
    app.UseExceptionHandler(options => options.Run(async context => {
        var error = context.Features.Get<IExceptionHandlerFeature>()?.Error;
        context.Response.StatusCode = error switch {
            NotFoundException => 404,
            BusinessRuleViolationException => 422,
            ConflictException => 409,
            _ => 500
        };
    }));

Here we register separate handlers per exception type with FastAPI.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from domain.exceptions import (
    DomainException,
    NotFoundException,
    BusinessRuleViolationException,
    ConflictException,
)

import structlog

logger = structlog.get_logger()


async def not_found_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    """
    NotFoundException → HTTP 404.
    Like catching NotFoundException in C# middleware and returning ProblemDetails.
    """
    logger.warning(
        "Resource not found",
        path=str(request.url),
        entity=exc.entity_name,
        entity_id=str(exc.entity_id),
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.4",
            "title": "Not Found",
            "status": 404,
            "detail": exc.message,
        },
    )


async def business_rule_exception_handler(
    request: Request, exc: BusinessRuleViolationException
) -> JSONResponse:
    """
    BusinessRuleViolationException → HTTP 422.
    Domain invariant was violated — like throwing InvalidOperationException in C#.
    """
    logger.warning(
        "Business rule violated",
        path=str(request.url),
        rule=exc.rule,
    )
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            "title": "Business Rule Violation",
            "status": 422,
            "detail": exc.message,
        },
    )


async def conflict_exception_handler(request: Request, exc: ConflictException) -> JSONResponse:
    """ConflictException → HTTP 409."""
    logger.warning("Conflict", path=str(request.url), error=exc.message)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.8",
            "title": "Conflict",
            "status": 409,
            "detail": exc.message,
        },
    )


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Catch-all for any DomainException not caught above → HTTP 400."""
    logger.warning("Domain error", path=str(request.url), error=exc.message)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            "title": "Bad Request",
            "status": 400,
            "detail": exc.message,
        },
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Pydantic validation errors → 422 with details.
    Like FluentValidation ProblemDetails in C# — returns structured error list.
    """
    logger.warning("Validation failed", path=str(request.url), errors=exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            "title": "Validation Error",
            "status": 422,
            "errors": exc.errors(),
        },
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Domain validation errors → 400 Bad Request (legacy fallback)."""
    logger.warning("Value error", path=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            "title": "Bad Request",
            "status": 400,
            "detail": str(exc),
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled exceptions → HTTP 500.
    Like the global exception handler middleware in ASP.NET Core.
    Never leaks internal details to the client.
    """
    logger.error(
        "Unhandled exception",
        path=str(request.url),
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.6.1",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred.",
        },
    )


