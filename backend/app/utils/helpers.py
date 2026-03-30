import uuid
import random
import string
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Callable, TypeVar
from functools import wraps
import re


T = TypeVar("T")

logger = logging.getLogger("flowra.helpers")


# =========================
# 🆔 ID GENERATORS
# =========================
def generate_uuid() -> str:
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_numeric_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))


# =========================
# 🕒 TIME HELPERS (TZ SAFE)
# =========================
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def add_minutes(minutes: int) -> datetime:
    return now_utc() + timedelta(minutes=minutes)


def add_days(days: int) -> datetime:
    return now_utc() + timedelta(days=days)


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    return dt.astimezone(timezone.utc).isoformat()


# =========================
# 🔐 SAFE ACCESS
# =========================
def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    return data.get(key, default)


# =========================
# 🔄 RETRY (PRODUCTION)
# =========================
def retry(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry with exponential backoff
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            _delay = delay

            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    if attempt == retries - 1:
                        logger.error(f"[RETRY FAILED] {func.__name__}: {e}")
                        raise

                    logger.warning(
                        f"[RETRY] {func.__name__} failed ({attempt+1}/{retries}) → retrying in {_delay}s"
                    )

                    time.sleep(_delay)
                    _delay *= backoff

        return wrapper

    return decorator


# =========================
# 🔢 NUMBER HELPERS
# =========================
def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


# =========================
# 🧠 STRING HELPERS
# =========================
def clean_string(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return value.strip()


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'\s+', '-', text)


# =========================
# 🔍 VALIDATION HELPERS
# =========================
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email))


def is_non_empty(value: Any) -> bool:
    return value is not None and value != ""


# =========================
# 📦 DICT HELPERS
# =========================
def remove_none(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {**a, **b}


# =========================
# ⏱️ PERFORMANCE TRACKING
# =========================
def measure_time(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start = time.perf_counter()

        result = func(*args, **kwargs)

        duration = time.perf_counter() - start
        logger.info(f"[PERF] {func.__name__} took {round(duration, 4)}s")

        return result

    return wrapper


# =========================
# 🔥 FEATURE FLAGS (DYNAMIC READY)
# =========================
FEATURE_FLAGS: Dict[str, bool] = {
    "AI_SCORING": True,
    "AUTO_FOLLOWUP": True,
    "ADVANCED_ANALYTICS": True,
}


def is_feature_enabled(flag: str) -> bool:
    return FEATURE_FLAGS.get(flag, False)


# =========================
# 📊 RANDOM (DEV ONLY)
# =========================
def random_value(min_val: int = 1000, max_val: int = 100000) -> int:
    return random.randint(min_val, max_val)


def random_probability() -> float:
    return round(random.uniform(0.1, 1.0), 2)


# =========================
# 🔐 REQUEST CONTEXT (ADVANCED)
# =========================
def generate_request_context() -> Dict[str, Any]:
    """
    Used for tracing requests across services
    """
    return {
        "request_id": generate_uuid(),
        "timestamp": now_utc().isoformat()
    }