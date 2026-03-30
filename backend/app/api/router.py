"""
API router — registers all versioned route modules.

The app is mounted at /api/v1 in main.py, so this router uses NO prefix.
All route modules are included with their own sub-prefixes.
"""

from fastapi import APIRouter

from app.core.config import settings

# ---------------------------------------------------------------------------
# Import route modules
# ---------------------------------------------------------------------------
from app.api.routes import auth
from app.api.routes import workspaces
from app.api.routes import contacts
from app.api.routes import deals
from app.api.routes import pipeline
from app.api.routes import analytics
from app.api.routes import automation
from app.api.routes import whatsapp
from app.api.routes import gmail
from app.api.routes import billing
from app.api.routes import notifications
from app.api.routes import calendar
from app.api.routes import tasks

# ---------------------------------------------------------------------------
# Root API router (no prefix — main.py mounts this at /api/v1)
# ---------------------------------------------------------------------------

api_router = APIRouter()

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@api_router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "env": settings.ENV,
    }


@api_router.get("/meta", tags=["System"])
def api_meta():
    """Returns feature flags useful for frontend configuration."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "features": {
            "whatsapp": bool(settings.WHATSAPP_TOKEN),
            "gmail": bool(settings.GOOGLE_CLIENT_ID),
            "billing": bool(settings.RAZORPAY_KEY_ID),
            "slack": bool(settings.SLACK_BOT_TOKEN),
            "notion": bool(settings.NOTION_API_KEY),
        },
    }


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

api_router.include_router(auth.router,          prefix="/auth",          tags=["Auth"])
api_router.include_router(workspaces.router,    prefix="/workspaces",    tags=["Workspaces"])
api_router.include_router(contacts.router,      prefix="/contacts",      tags=["Contacts"])
api_router.include_router(deals.router,         prefix="/deals",         tags=["Deals"])
api_router.include_router(pipeline.router,      prefix="/pipelines",     tags=["Pipelines"])
api_router.include_router(analytics.router,     prefix="/analytics",     tags=["Analytics"])
api_router.include_router(automation.router,    prefix="/automation",    tags=["Automation"])
api_router.include_router(whatsapp.router,      prefix="/whatsapp",      tags=["WhatsApp"])
api_router.include_router(gmail.router,         prefix="/gmail",         tags=["Gmail"])
api_router.include_router(billing.router,       prefix="/billing",       tags=["Billing"])
api_router.include_router(notifications.router, prefix="/notifications",  tags=["Notifications"])
api_router.include_router(calendar.router,      prefix="/calendar",       tags=["Calendar"])
api_router.include_router(tasks.router,         prefix="/tasks",          tags=["Tasks"])
