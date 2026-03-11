"""
Application entry point — equivalent to Program.cs in ASP.NET Core.

In C# you have:
    var builder = WebApplication.CreateBuilder(args);
    builder.Services.AddControllers();
    builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();
    builder.Services.AddMediatR(cfg => {
        cfg.RegisterServicesFromAssembly(typeof(CreateOrderCommandHandler).Assembly);
        cfg.AddBehavior<LoggingBehavior>();
    });
    builder.Host.UseSerilog();
    var app = builder.Build();
    app.UseCorrelationId();
    app.UseExceptionHandler();
    app.MapControllers();
    app.Run();

Here we do the same with FastAPI + dependency-injector + Mediatr + Structlog.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

from infrastructure.config import settings
from infrastructure.logging import configure_logging
from infrastructure.container import Container, create_mediator
from infrastructure.persistence.database import engine
from infrastructure.persistence.models import Base

from presentation.api import order_routes, health_routes
from presentation.middleware.correlation_id import CorrelationIdMiddleware
from presentation.middleware.exception_handlers import (
    global_exception_handler,
    not_found_exception_handler,
    business_rule_exception_handler,
    conflict_exception_handler,
    domain_exception_handler,
    validation_exception_handler,
    value_error_handler,
)

from domain.exceptions import (
    DomainException,
    NotFoundException,
    BusinessRuleViolationException,
    ConflictException,
)

import structlog

# ── Configure structured logging (like builder.Host.UseSerilog()) ─────────
configure_logging()
logger = structlog.get_logger()


# ── Lifespan (startup / shutdown) ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Equivalent to:
        builder.Services.AddDbContext(...)   // startup
        app.Lifetime.ApplicationStopping     // shutdown

    The lifespan context manager handles startup/shutdown events.
    In .NET this would be IHostedService or IHostApplicationLifetime.
    """
    logger.info("Starting application", app_name=settings.APP_NAME)

    # Create tables (in production, use Alembic migrations instead)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")

    yield  # ← App runs here (handles requests)

    # Shutdown — like app.Lifetime.ApplicationStopping
    await engine.dispose()
    logger.info("Application shut down gracefully")


# ── Build the app (like WebApplication.CreateBuilder) ─────────────────────

def create_app() -> FastAPI:
    """
    Application factory — equivalent to Program.cs in ASP.NET Core.

    This is where we:
    1. Configure DI container     (builder.Services.Add...)
    2. Create Mediator pipeline   (builder.Services.AddMediatR(...))
    3. Build the FastAPI app       (builder.Build())
    4. Register middleware         (app.Use...)
    5. Register exception handlers (app.UseExceptionHandler())
    6. Map routes                  (app.MapControllers())
    """

    # ── 1. Wire up DI container (like builder.Services in C#) ─────────
    container = Container()

    # ── 2. Create Mediator with DI-aware handler resolution + behaviors
    mediator = create_mediator(container)

    # ── 3. Build the FastAPI app ──────────────────────────────────────
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Clean Architecture in Python — a .NET developer's guide",
        lifespan=lifespan,
        docs_url="/swagger",       # Swagger UI at /swagger (like Swashbuckle)
        redoc_url="/redoc",
    )

    # Store container & mediator on app state (for access in routes & tests)
    app.state.container = container
    app.state.mediator = mediator

    # ── 4. Register middleware (like app.Use... in C#) ────────────────
    # Order matters! Like the middleware pipeline in ASP.NET Core.
    app.add_middleware(CorrelationIdMiddleware)  # like app.UseCorrelationId()

    # ── 5. Register exception handlers (like app.UseExceptionHandler) ─
    # More specific exceptions must be registered BEFORE more general ones.
    # This is like the exception handler middleware in ASP.NET Core that
    # maps specific exception types to HTTP status codes.
    app.add_exception_handler(NotFoundException, not_found_exception_handler)
    app.add_exception_handler(BusinessRuleViolationException, business_rule_exception_handler)
    app.add_exception_handler(ConflictException, conflict_exception_handler)
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # ── 6. Register routes (like app.MapControllers) ──────────────────
    app.include_router(health_routes.router)
    app.include_router(order_routes.router)

    logger.info(
        "Application configured",
        swagger="/swagger",
        redoc="/redoc",
        endpoints=["/health", "/api/orders"],
    )
    return app


app = create_app()


# ── Run with: python -m uvicorn main:app --reload ────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
