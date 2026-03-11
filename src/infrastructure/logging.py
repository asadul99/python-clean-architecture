"""
Structlog configuration — equivalent to Serilog setup in Program.cs.
Provides structured JSON logging with correlation IDs.
"""

import logging
import structlog

from infrastructure.config import settings


def configure_logging() -> None:
    """
    Call once at startup — like builder.Host.UseSerilog() in C#.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,          # correlation-id support
            structlog.processors.add_log_level,               # adds 'level' field
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),      # ISO timestamps
            structlog.processors.JSONRenderer() if not settings.DEBUG
            else structlog.dev.ConsoleRenderer(),             # pretty in dev, JSON in prod
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

