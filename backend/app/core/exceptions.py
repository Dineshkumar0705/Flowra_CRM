"""
Flowra custom exception hierarchy.

Every exception in the codebase inherits from FlowraException.
This gives us:
- Consistent error codes for the frontend
- Centralised HTTP status mapping
- Structured logging without boilerplate
"""

from typing import Any, Dict, Optional


class FlowraException(Exception):
    """Base exception for all Flowra business logic errors."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# 404 – Not found
# ---------------------------------------------------------------------------

class NotFoundError(FlowraException):
    """Resource does not exist (or has been soft-deleted)."""

    def __init__(self, resource: str, identifier: Any = None) -> None:
        detail = f" with id '{identifier}'" if identifier else ""
        super().__init__(
            message=f"{resource}{detail} not found.",
            code=f"{resource.upper().replace(' ', '_')}_NOT_FOUND",
            status_code=404,
        )


# ---------------------------------------------------------------------------
# 401 / 403 – Auth
# ---------------------------------------------------------------------------

class UnauthorizedError(FlowraException):
    """Missing or invalid authentication credentials."""

    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(message=message, code="UNAUTHORIZED", status_code=401)


class ForbiddenError(FlowraException):
    """Authenticated but insufficient permissions."""

    def __init__(self, message: str = "You don't have permission to perform this action.") -> None:
        super().__init__(message=message, code="FORBIDDEN", status_code=403)


# ---------------------------------------------------------------------------
# 400 – Validation / business logic
# ---------------------------------------------------------------------------

class ValidationError(FlowraException):
    """Input failed business-rule validation (distinct from Pydantic 422)."""

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class ConflictError(FlowraException):
    """Resource already exists or state conflict."""

    def __init__(self, resource: str, message: Optional[str] = None) -> None:
        super().__init__(
            message=message or f"{resource} already exists.",
            code=f"{resource.upper().replace(' ', '_')}_CONFLICT",
            status_code=409,
        )


class BusinessRuleError(FlowraException):
    """A domain business rule was violated."""

    def __init__(self, message: str, code: str = "BUSINESS_RULE_VIOLATION") -> None:
        super().__init__(message=message, code=code, status_code=400)


# ---------------------------------------------------------------------------
# 402 – Billing
# ---------------------------------------------------------------------------

class PlanLimitError(FlowraException):
    """Workspace has hit a plan limit."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="PLAN_LIMIT_EXCEEDED", status_code=402)


class BillingError(FlowraException):
    """General billing / payment error."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="BILLING_ERROR", status_code=402)


# ---------------------------------------------------------------------------
# 503 – External integrations
# ---------------------------------------------------------------------------

class IntegrationError(FlowraException):
    """An external API call failed (WhatsApp, Gmail, Slack, Notion, etc.)."""

    def __init__(self, integration: str, message: str) -> None:
        super().__init__(
            message=f"{integration} integration error: {message}",
            code=f"{integration.upper()}_INTEGRATION_ERROR",
            status_code=503,
        )


# ---------------------------------------------------------------------------
# 500 – Internal
# ---------------------------------------------------------------------------

class InternalError(FlowraException):
    """Unexpected internal server error — should never reach the user."""

    def __init__(self, message: str = "An unexpected error occurred.") -> None:
        super().__init__(message=message, code="INTERNAL_ERROR", status_code=500)
