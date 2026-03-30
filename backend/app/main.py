"""
Flowra FastAPI application entry point.

Startup sequence:
  1. Configure structlog (JSON in prod, coloured console in dev)
  2. Verify DB connectivity (does NOT create tables — use Alembic)
  3. Register exception handlers
  4. Mount CORS, rate-limiting, and logging middleware
  5. Mount the versioned API router at /api/v1
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import FlowraException

log = logging.getLogger("flowra.main")


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Configure structured logging first
    from app.core.logging import configure_logging
    configure_logging()

    # 🔥 SAFE LOG (no kwargs → no crash)
    log.info(f"flowra.startup | env={settings.ENV} | version={settings.VERSION}")

    # 2. Verify DB is reachable (non-fatal)
    from app.core.database import check_db_connection

    try:
        if check_db_connection():
            log.info("db.connected")
        else:
            log.warning("db.connection_failed")
    except Exception as e:
        log.error(f"db.check_error: {str(e)}")

    yield

    log.info("flowra.shutdown")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "AI-powered CRM SaaS for Indian agencies & freelancers. "
            "Multi-workspace, WhatsApp-native, Razorpay billing."
        ),
        docs_url="/docs" if settings.ENV != "production" else None,
        redoc_url="/redoc" if settings.ENV != "production" else None,
        openapi_url="/openapi.json" if settings.ENV != "production" else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Request logging middleware
    # ------------------------------------------------------------------
    from app.middleware.logging_middleware import RequestLoggingMiddleware
    app.add_middleware(RequestLoggingMiddleware)

    # ------------------------------------------------------------------
    # Rate limiting (slowapi)
    # ------------------------------------------------------------------
    try:
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.util import get_remote_address
        from slowapi.errors import RateLimitExceeded
        from slowapi.middleware import SlowAPIMiddleware

        limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
        app.state.limiter = limiter

        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)

        log.info("rate_limiting.enabled")

    except ImportError:
        log.warning("rate_limiting.disabled — slowapi not installed")

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------

    @app.exception_handler(FlowraException)
    async def flowra_exception_handler(request: Request, exc: FlowraException) -> JSONResponse:
        log.warning(f"flowra.error | code={exc.code} | message={exc.message}")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "message": exc.message,
                "error": {
                    "code": exc.code,
                    "details": exc.details or {},
                },
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "data": None,
                "message": "The requested resource was not found.",
                "error": {"code": "NOT_FOUND", "details": {}},
            },
        )

    @app.exception_handler(405)
    async def method_not_allowed_handler(request: Request, exc) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            content={
                "success": False,
                "data": None,
                "message": "Method not allowed.",
                "error": {"code": "METHOD_NOT_ALLOWED", "details": {}},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # 🔥 FULL TRACE LOG
        log.exception("flowra.unhandled_exception")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "data": None,
                "message": "An internal server error occurred.",
                "error": {"code": "INTERNAL_ERROR", "details": {}},
            },
        )

    # ------------------------------------------------------------------
    # Pydantic validation errors
    # ------------------------------------------------------------------
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:

        errors = []
        for e in exc.errors():
            field = ".".join(str(loc) for loc in e["loc"] if loc != "body")
            errors.append({
                "field": field,
                "message": e["msg"]
            })

        log.warning(f"validation.error | count={len(errors)} | errors={errors}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "data": None,
                "message": "Request validation failed.",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "details": {"errors": errors},
                },
            },
        )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    from app.api.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    # Root
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    return app


app = create_application()