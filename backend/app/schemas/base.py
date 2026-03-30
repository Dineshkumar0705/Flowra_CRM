"""
Shared Pydantic base and response envelope helpers.

All schemas inherit from FlowraSchema so we get:
  - from_attributes=True  (ORM mode)
  - populate_by_name=True (alias support)
  - use_enum_values=True  (serialize enums as strings)

Response envelopes follow the API spec:
  { "success": true, "data": ..., "message": "...", "meta": {...} }
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


# ---------------------------------------------------------------------------
# Base schema
# ---------------------------------------------------------------------------

class FlowraSchema(BaseModel):
    """Base class for every Pydantic schema in Flowra."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


# ---------------------------------------------------------------------------
# Pagination meta
# ---------------------------------------------------------------------------

class PaginationMeta(FlowraSchema):
    page: int
    per_page: int
    total: int
    total_pages: int


# ---------------------------------------------------------------------------
# Standard response envelopes
# ---------------------------------------------------------------------------

class SuccessResponse(FlowraSchema, Generic[DataT]):
    """Single-item success response."""

    success: bool = True
    message: str = "Success"
    data: DataT


class PaginatedResponse(FlowraSchema, Generic[DataT]):
    """Paginated list response."""

    success: bool = True
    message: str = "Success"
    data: List[DataT]
    meta: PaginationMeta


class ErrorDetail(FlowraSchema):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(FlowraSchema):
    """Standard error response."""

    success: bool = False
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def success(data: Any, message: str = "Success") -> dict:
    """Build a success response dict."""
    return {"success": True, "message": message, "data": data}


def paginated(
    data: List[Any],
    total: int,
    page: int,
    per_page: int,
    message: str = "Success",
) -> dict:
    """Build a paginated response dict."""
    total_pages = (total + per_page - 1) // per_page if per_page else 0
    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }
