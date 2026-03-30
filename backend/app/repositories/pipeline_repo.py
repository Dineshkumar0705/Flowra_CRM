"""Pipeline and Stage repository."""

import logging
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.deal import Deal
from app.models.pipeline import DealPipelineMap, Pipeline, PipelineStage

log = logging.getLogger("flowra.repo.pipeline")


class PipelineRepository:
    """CRUD for Pipeline, PipelineStage, and DealPipelineMap tables."""

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Pipeline CRUD
    # ------------------------------------------------------------------

    def create_pipeline(self, data: dict) -> Pipeline:
        data["workspace_id"] = self.workspace_id
        pipeline = Pipeline(**data)
        self.db.add(pipeline)
        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        return (
            self.db.query(Pipeline)
            .filter(
                Pipeline.id == pipeline_id,
                Pipeline.workspace_id == self.workspace_id,
                Pipeline.is_active == True,
            )
            .first()
        )

    def list_pipelines(self) -> List[Pipeline]:
        return (
            self.db.query(Pipeline)
            .filter(
                Pipeline.workspace_id == self.workspace_id,
                Pipeline.is_active == True,
            )
            .order_by(Pipeline.is_default.desc(), Pipeline.created_at.asc())
            .all()
        )

    def update_pipeline(self, pipeline: Pipeline, data: dict) -> Pipeline:
        from datetime import datetime, timezone
        for k, v in data.items():
            if hasattr(pipeline, k):
                setattr(pipeline, k, v)
        pipeline.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline

    def deactivate_pipeline(self, pipeline: Pipeline) -> None:
        pipeline.is_active = False
        self.db.commit()

    # ------------------------------------------------------------------
    # Stage CRUD
    # ------------------------------------------------------------------

    def create_stage(self, data: dict) -> PipelineStage:
        stage = PipelineStage(**data)
        self.db.add(stage)
        self.db.commit()
        self.db.refresh(stage)
        return stage

    def get_stage(self, stage_id: str) -> Optional[PipelineStage]:
        return self.db.query(PipelineStage).filter(PipelineStage.id == stage_id).first()

    def list_stages(self, pipeline_id: str) -> List[PipelineStage]:
        return (
            self.db.query(PipelineStage)
            .filter(PipelineStage.pipeline_id == pipeline_id)
            .order_by(PipelineStage.order.asc())
            .all()
        )

    def update_stage(self, stage: PipelineStage, data: dict) -> PipelineStage:
        for k, v in data.items():
            if hasattr(stage, k):
                setattr(stage, k, v)
        self.db.commit()
        self.db.refresh(stage)
        return stage

    def delete_stage(self, stage: PipelineStage) -> None:
        self.db.delete(stage)
        self.db.commit()

    # ------------------------------------------------------------------
    # DealPipelineMap
    # ------------------------------------------------------------------

    def map_deal(self, deal_id: str, pipeline_id: str, stage_id: str, position: int = 0) -> DealPipelineMap:
        mapping = DealPipelineMap(
            deal_id=deal_id, pipeline_id=pipeline_id, stage_id=stage_id, position=position
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def get_mapping(self, deal_id: str, pipeline_id: str) -> Optional[DealPipelineMap]:
        return (
            self.db.query(DealPipelineMap)
            .filter(DealPipelineMap.deal_id == deal_id, DealPipelineMap.pipeline_id == pipeline_id)
            .first()
        )

    def move_deal(self, mapping: DealPipelineMap, new_stage_id: str, position: int = 0) -> DealPipelineMap:
        mapping.move_to_stage(new_stage_id)
        mapping.position = position
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def get_board(self, pipeline_id: str) -> Dict[str, List[Deal]]:
        """
        Return a dict of {stage_id: [Deal, ...]} for the Kanban board.
        One SQL join — no N+1.
        """
        rows = (
            self.db.query(DealPipelineMap, Deal)
            .join(Deal, Deal.id == DealPipelineMap.deal_id)
            .filter(
                DealPipelineMap.pipeline_id == pipeline_id,
                Deal.deleted_at.is_(None),
            )
            .order_by(DealPipelineMap.position.asc())
            .all()
        )
        board: Dict[str, List[Deal]] = {}
        for mapping, deal in rows:
            sid = mapping.stage_id or "__unassigned__"
            board.setdefault(sid, []).append(deal)
        return board

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def stage_values(self, pipeline_id: str) -> Dict[str, float]:
        rows = (
            self.db.query(DealPipelineMap.stage_id, func.sum(Deal.value))
            .join(Deal, Deal.id == DealPipelineMap.deal_id)
            .filter(DealPipelineMap.pipeline_id == pipeline_id, Deal.deleted_at.is_(None))
            .group_by(DealPipelineMap.stage_id)
            .all()
        )
        return {str(sid): float(v or 0) for sid, v in rows}
