"""
Structured logging configuration using structlog.

Wire once at application startup via `configure_logging()`.
All modules should use:

    import logging
    log = logging.getLogger("flowra.<module>")
    log.info("event.name", key=value, ...)

In production (ENV=production) output is JSON.
In development it's coloured console output.
"""

import logging
import sys
from typing import Any

import structlog

from app.core.config import settings


def _patch_stdlib_logger() -> None:
    """
    Allow structlog-style keyword arguments in stdlib log calls.

    All service/repo modules use:
        log = logging.getLogger("flowra.x")
        log.info("event", user_id=x, workspace_id=y)

    Standard Python loggers only accept exc_info/extra/stack_info/stacklevel
    as kwargs.  This patch makes any extra kwargs get appended to the message
    as "key=value" pairs so the calls work without touching every file.
    """
    _original_log = logging.Logger._log

    def _kwarg_friendly_log(
        self,
        level: int,
        msg: object,
        args: Any,
        exc_info: Any = None,
        extra: Any = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        **kwargs: Any,
    ) -> None:
        if kwargs:
            kv = " ".join(f"{k}={v!r}" for k, v in kwargs.items())
            msg = f"{msg} {kv}"
        _original_log(
            self, level, msg, args,
            exc_info=exc_info, extra=extra,
            stack_info=stack_info, stacklevel=stacklevel,
        )

    logging.Logger._log = _kwarg_friendly_log  # type: ignore[method-assign]


# Patch immediately so modules that import logging before configure_logging()
# also benefit.
_patch_stdlib_logger()


def configure_logging() -> None:
    """
    Configure structlog + standard library logging.
    Call once at application startup (inside lifespan).
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Shared processors for both dev and prod
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.ENV == "production":
        # JSON output for log aggregators (Datadog, Loki, CloudWatch)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=processors,
        )
    else:
        # Human-readable coloured output for local dev
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=processors,
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_request_logger(request_id: str, path: str, method: str) -> Any:
    """Return a logger bound with HTTP request context."""
    return structlog.get_logger("flowra.request").bind(
        request_id=request_id,
        path=path,
        method=method,
    )
