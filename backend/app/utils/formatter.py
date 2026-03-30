from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from decimal import Decimal
import uuid


# =========================
# 🔥 REQUEST TRACE (CRITICAL)
# =========================
def generate_request_id() -> str:
    return str(uuid.uuid4())


# =========================
# 🧱 BASE RESPONSE FORMAT
# =========================
def success_response(
    data: Any = None,
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:

    return {
        "status": "success",
        "message": message,
        "data": data,
        "meta": meta or {},
        "request_id": request_id or generate_request_id()
    }


def error_response(
    message: str = "Something went wrong",
    code: int = 400,
    error_type: str = "API_ERROR",
    details: Optional[Any] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:

    return {
        "status": "error",
        "message": message,
        "code": code,
        "error_type": error_type,
        "details": details,
        "request_id": request_id or generate_request_id()
    }


# =========================
# 📦 PAGINATION FORMAT
# =========================
def paginated_response(
    items: List[Any],
    total: int,
    limit: int,
    offset: int
) -> Dict[str, Any]:

    return success_response(
        data=items,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }
    )


# =========================
# 🧠 SAFE SERIALIZER
# =========================
def _serialize_value(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, list):
        return [_serialize_value(v) for v in value]

    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}

    return value


def serialize_model(obj: Any) -> Dict[str, Any]:
    """
    SQLAlchemy → dict (safe + nested ready)
    """

    if obj is None:
        return {}

    data = {}

    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        data[column.name] = _serialize_value(value)

    return data


def serialize_list(objs: List[Any]) -> List[Dict[str, Any]]:
    return [serialize_model(obj) for obj in objs]


# =========================
# 💰 CURRENCY FORMAT
# =========================
def format_currency(value: Union[int, float, Decimal], currency: str = "INR") -> str:

    if value is None:
        return "0"

    value = float(value)

    if currency == "INR":
        return f"₹{value:,.0f}"
    elif currency == "USD":
        return f"${value:,.2f}"

    return f"{value}"


# =========================
# 📊 PERCENTAGE FORMAT
# =========================
def format_percentage(value: Union[int, float, None]) -> float:
    return round(float(value or 0), 2)


# =========================
# 🧠 DEAL FORMATTER
# =========================
def format_deal(deal: Any) -> Dict[str, Any]:

    return {
        "id": deal.id,
        "title": deal.title,
        "value": float(deal.value),
        "formatted_value": format_currency(deal.value),
        "stage": deal.stage.value if deal.stage else None,
        "priority": deal.priority.value if deal.priority else None,
        "probability": format_percentage(deal.probability),
        "ai_score": getattr(deal, "ai_score", None),
        "created_at": _serialize_value(deal.created_at),
        "updated_at": _serialize_value(deal.updated_at),
    }


def format_deal_list(deals: List[Any]) -> List[Dict[str, Any]]:
    return [format_deal(d) for d in deals]


# =========================
# 📊 PIPELINE FORMATTER
# =========================
def format_pipeline(data: Dict[str, Any]) -> Dict[str, Any]:

    return {
        "pipeline_id": data.get("pipeline_id"),
        "pipeline_name": data.get("pipeline_name"),
        "stages": [
            {
                "stage_id": s.get("stage_id"),
                "stage_name": s.get("stage_name"),
                "deal_count": s.get("deal_count", 0),
                "total_value": s.get("total_value", 0),
                "formatted_value": format_currency(s.get("total_value", 0)),
                "deals": s.get("deals", [])
            }
            for s in data.get("stages", [])
        ]
    }


# =========================
# 📈 ANALYTICS FORMATTER
# =========================
def format_analytics(data: Dict[str, Any]) -> Dict[str, Any]:

    return {
        "total_deals": data.get("total_deals", 0),
        "won_deals": data.get("won_deals", 0),
        "lost_deals": data.get("lost_deals", 0),
        "conversion_rate": format_percentage(data.get("conversion_rate")),
        "total_value": data.get("total_value", 0),
        "formatted_total_value": format_currency(data.get("total_value", 0)),
        "won_value": data.get("won_value", 0),
        "formatted_won_value": format_currency(data.get("won_value", 0)),
    }


# =========================
# 🧾 CLEAN NULLS
# =========================
def clean_nulls(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


# =========================
# 🔥 UNIVERSAL FORMATTER
# =========================
def format_response(
    data: Any,
    message: str = "Success"
) -> Dict[str, Any]:

    if isinstance(data, list):
        return success_response(data=data, message=message)

    if isinstance(data, dict):
        return success_response(data=clean_nulls(data), message=message)

    return success_response(data=data, message=message)