"""
Dependency Injection Container — equivalent to IServiceCollection / Program.cs in C#.

In .NET you write:
    builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();
    builder.Services.AddScoped<IOrderRepository, OrderRepository>();
    builder.Services.AddMediatR(cfg => {
        cfg.RegisterServicesFromAssembly(typeof(CreateOrderCommandHandler).Assembly);
        cfg.AddBehavior<LoggingBehavior>();
        cfg.AddBehavior<PerformanceBehavior>();
    });

Here we do the same thing with dependency-injector:
    uow = providers.Factory(UnitOfWork, session_factory=...)

The handler_class_manager bridges MediatR ↔ DI Container:
    When Mediator needs to create a handler, it calls handler_class_manager(HandlerCls).
    We override this to resolve the handler from our DI container, injecting dependencies.
"""

from dependency_injector import containers, providers
from mediatr import Mediator

from infrastructure.persistence.database import async_session_factory
from infrastructure.repositories.unit_of_work import UnitOfWork
from application.behaviors import LoggingBehavior, PerformanceBehavior

# Import ALL handlers so the @Mediator.handler decorators run and register them.
# This is like services.AddMediatR(typeof(CreateOrderCommandHandler).Assembly) in C#.
import application.use_cases.orders.create_order        # noqa: F401
import application.use_cases.orders.get_orders           # noqa: F401
import application.use_cases.orders.delete_order         # noqa: F401
import application.use_cases.orders.update_order         # noqa: F401
import application.use_cases.orders.change_order_status  # noqa: F401


class Container(containers.DeclarativeContainer):
    """
    Root composition root — like IServiceCollection in .NET.
    Everything is wired here; no 'new' keyword scattered across the codebase.

    In C# you'd have:
        builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();
        builder.Services.AddScoped<IOrderRepository, OrderRepository>();
        builder.Services.AddSingleton<LoggingBehavior>();

    Here each providers.Factory(...) is like services.AddTransient/AddScoped:
        - Factory = Transient (new instance each call)
        - Singleton = Singleton
        - Object = pre-existing instance
    """

    wiring_config = containers.WiringConfiguration(
        modules=[
            "presentation.api.order_routes",
            "presentation.api.health_routes",
        ]
    )

    # ── Infrastructure ────────────────────────────────────────────────

    # Equivalent to: services.AddDbContext<AppDbContext>(options => ...)
    session_factory = providers.Object(async_session_factory)

    # Equivalent to: services.AddScoped<IUnitOfWork, UnitOfWork>()
    unit_of_work = providers.Factory(
        UnitOfWork,
        session_factory=session_factory,
    )

    # ── Pipeline Behaviors (like services.AddMediatR(cfg => cfg.AddBehavior<>()))
    logging_behavior = providers.Singleton(LoggingBehavior)
    performance_behavior = providers.Singleton(PerformanceBehavior)


def create_mediator(container: Container) -> Mediator:
    """
    Create a Mediator instance with a custom handler_class_manager that
    resolves handler dependencies from our DI container.

    This is the bridge between MediatR and dependency-injector:
    - In C# MediatR, the DI container auto-resolves handler constructor params.
    - Here, handler_class_manager does the same thing.

    Pipeline behaviors are applied as decorating wrappers around the handler,
    just like IPipelineBehavior<TRequest, TResponse> in C# MediatR.
    """

    # Resolve pipeline behaviors from container (singletons)
    logging_behavior = container.logging_behavior()
    performance_behavior = container.performance_behavior()

    def handler_class_manager(handler_cls: type, is_behavior: bool = False):
        """
        Called by Mediator when it needs to instantiate a handler class.
        Instead of calling HandlerCls() with no args (the default),
        we inject the UnitOfWork from the DI container.
        """
        # Resolve a fresh UnitOfWork from the container for each request
        uow = container.unit_of_work()
        handler = handler_cls(uow=uow)

        # Wrap the handler with pipeline behaviors (like IPipelineBehavior chain)
        original_handle = handler.handle

        async def wrapped_handle(request):
            # Behavior chain: Logging → Performance → actual Handler
            async def run_performance():
                return await performance_behavior.handle(
                    request, lambda: original_handle(request)
                )

            return await logging_behavior.handle(request, run_performance)

        handler.handle = wrapped_handle
        return handler

    return Mediator(handler_class_manager=handler_class_manager)

