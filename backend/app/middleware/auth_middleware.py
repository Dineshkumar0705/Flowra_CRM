import uuid
from typing import Callable, Optional, Dict, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status

from app.core.security import decode_token


# =========================
# 🧠 HELPER: EXTRACT TOKEN
# =========================
def extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        return None

    return auth_header.split(" ")[1]


# =========================
# 🧠 HELPER: BUILD USER CONTEXT
# =========================
def build_user_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(payload.get("sub")),
        "role": payload.get("role", "user"),
        "org_id": payload.get("org_id", 1),
        "token_type": payload.get("type")
    }


# =========================
# 🔐 DEV MODE MIDDLEWARE
# =========================
class AuthMiddleware(BaseHTTPMiddleware):
    """
    🔓 Non-blocking middleware (DEV MODE)

    ✔ Attaches user if token present
    ✔ Does NOT block request
    ✔ Safe for Swagger testing
    ✔ Adds request tracing
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # =========================
        # 🆔 REQUEST ID (IMPORTANT)
        # =========================
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # =========================
        # DEFAULT STATE
        # =========================
        request.state.user = None
        request.state.org = None

        # =========================
        # 🔑 TOKEN EXTRACTION
        # =========================
        token = extract_bearer_token(
            request.headers.get("Authorization")
        )

        if token:
            try:
                payload = decode_token(token)
                user = build_user_context(payload)

                request.state.user = user
                request.state.org = {
                    "id": user["org_id"]
                }

            except Exception:
                # Dev mode → ignore errors
                request.state.user = None

        # =========================
        # 🚀 PROCESS REQUEST
        # =========================
        response: Response = await call_next(request)

        # =========================
        # 🧾 ADD DEBUG HEADERS
        # =========================
        response.headers["X-Request-ID"] = request_id

        return response


# =========================
# 🚨 STRICT PRODUCTION MODE
# =========================
class StrictAuthMiddleware(BaseHTTPMiddleware):
    """
    🔒 Production-grade auth enforcement

    ✔ Blocks unauthorized requests
    ✔ Validates token
    ✔ Attaches user context
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        token = extract_bearer_token(
            request.headers.get("Authorization")
        )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token"
            )

        try:
            payload = decode_token(token)
            user = build_user_context(payload)

            request.state.user = user
            request.state.org = {
                "id": user["org_id"]
            }

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


# =========================
# 🧠 OPTIONAL HELPERS
# =========================
def get_request_user(request: Request) -> Optional[Dict[str, Any]]:
    return getattr(request.state, "user", None)


def get_request_org(request: Request) -> Optional[Dict[str, Any]]:
    return getattr(request.state, "org", None)


# =========================
# 🔮 FUTURE UPGRADES
# =========================
# - 🔥 Rate limiting (Redis)
# - 📊 Request logging (ELK / Datadog)
# - 🧾 Audit logs (who did what)
# - 🌍 Multi-tenant DB routing
# - 🚨 Suspicious activity detection
# - 🧠 AI anomaly detection (future 🔥 feature)