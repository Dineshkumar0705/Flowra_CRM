"""
Request/response logging middleware.

Logs every HTTP request with: method, path, status_code, duration_ms, request_id.
Attaches request_id to structlog context for correlation across log lines.
"""

import time
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

log = logging.getLogger("flowra.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing and correlation ID."""

    SKIP_PATHS = {"/api/v1/health", "/api/v1/meta", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip health checks to avoid log spam
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        start = time.perf_counter()

        # Bind context vars so all log lines within this request share the ID
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            log.error(
                "http.request_error",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                },
                exc_info=True,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        log.info(
            "http.request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response
