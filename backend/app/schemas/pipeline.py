"""Pipeline and Stage Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from app.schemas.base import FlowraSchema


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class PipelineCreate(FlowraSchema):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    is_default: bool = False
    settings: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()


class PipelineUpdate(FlowraSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class PipelineResponse(FlowraSchema):
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    is_default: bool
    is_active: bool
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Stage
# ---------------------------------------------------------------------------

class StageCreate(FlowraSchema):
    name: str = Field(..., min_length=1, max_length=100)
    order: int = Field(..., ge=0)
    probability: float = Field(default=0.0, ge=0, le=100)
    color: str = Field(default="#3B82F6")
    is_won_stage: bool = False
    is_lost_stage: bool = False
    automation_rules: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not v.startswith("#") or len(v) not in (4, 7):
            raise ValueError("Color must be a hex code like #3B82F6 or #FFF.")
        return v.upper()


class StageUpdate(FlowraSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    order: Optional[int] = Field(None, ge=0)
    probability: Optional[float] = Field(None, ge=0, le=100)
    color: Optional[str] = None
    is_won_stage: Optional[bool] = None
    is_lost_stage: Optional[bool] = None
    automation_rules: Optional[Dict[str, Any]] = None


class StageResponse(FlowraSchema):
    id: str
    pipeline_id: str
    name: str
    order: int
    probability: float
    color: str
    is_won_stage: bool
    is_lost_stage: bool
    automation_rules: Dict[str, Any]
    created_at: datetime


# ---------------------------------------------------------------------------
# Kanban / board
# ---------------------------------------------------------------------------

class MoveDealRequest(FlowraSchema):
    deal_id: str
    stage_id: str
    position: int = 0


class ReorderDealsRequest(FlowraSchema):
    stage_id: str
    deal_ids: List[str]   # ordered list — index 0 = top of column


class KanbanColumn(FlowraSchema):
    stage: StageResponse
    deal_ids: List[str]
    total_value: float
    deal_count: int


class PipelineBoardResponse(FlowraSchema):
    pipeline: PipelineResponse
    columns: List[KanbanColumn]


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------
PipelineOut = PipelineResponse
PipelineStageCreate = StageCreate
PipelineStageUpdate = StageUpdate
PipelineStageOut = StageResponse
KanbanBoardOut = PipelineBoardResponse
