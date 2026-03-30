"""Deal Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from app.models.deal import DealPriority, DealStage
from app.schemas.base import FlowraSchema


class DealCreate(FlowraSchema):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    value: float = Field(default=0.0, ge=0)
    currency: str = Field(default="INR", max_length=10)
    stage: DealStage = DealStage.NEW
    priority: DealPriority = DealPriority.MEDIUM
    probability: float = Field(default=0.0, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    owner_id: Optional[str] = None
    contact_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be blank.")
        return v

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("tags")
    @classmethod
    def normalise_tags(cls, v: List[str]) -> List[str]:
        return list({t.strip().lower() for t in v if t.strip()})


class DealUpdate(FlowraSchema):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    value: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    stage: Optional[DealStage] = None
    priority: Optional[DealPriority] = None
    probability: Optional[float] = Field(None, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    owner_id: Optional[str] = None
    contact_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    ai_score: Optional[float] = None
    ai_notes: Optional[str] = None


class DealStageMove(FlowraSchema):
    """Request body for moving a deal to a new stage."""
    stage: DealStage


class DealResponse(FlowraSchema):
    id: str
    workspace_id: str
    title: str
    description: Optional[str] = None
    value: float
    currency: str
    stage: DealStage
    priority: DealPriority
    probability: float
    expected_close_date: Optional[datetime] = None
    owner_id: Optional[str] = None
    contact_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    source: Optional[str] = None
    tags: List[str]
    custom_fields: Dict[str, Any]
    ai_score: Optional[float] = None
    ai_notes: Optional[str] = None
    won_at: Optional[datetime] = None
    lost_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DealFilters(FlowraSchema):
    stage: Optional[DealStage] = None
    priority: Optional[DealPriority] = None
    owner_id: Optional[str] = None
    contact_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    search: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------
DealOut = DealResponse
MoveStagRequest = DealStageMove
