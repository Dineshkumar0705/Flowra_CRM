"""Pipeline and Kanban board service."""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.pipeline import Pipeline, PipelineStage
from app.repositories.pipeline_repo import PipelineRepository
from app.schemas.pipeline import PipelineCreate, PipelineUpdate, StageCreate, StageUpdate

log = logging.getLogger("flowra.service.pipeline")


class PipelineService:
    """Business logic for Pipeline, Stage, and Kanban board management."""

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.repo = PipelineRepository(db, workspace_id)
        self.workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Pipeline CRUD
    # ------------------------------------------------------------------

    def create_pipeline(self, payload: PipelineCreate) -> Pipeline:
        data = payload.model_dump(exclude_unset=False)

        # Only one default pipeline allowed per workspace
        if data.get("is_default"):
            self._clear_default_flag()

        pipeline = self.repo.create_pipeline(data)
        log.info("pipeline.created", workspace=self.workspace_id, pipeline_id=pipeline.id)
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        pipeline = self.repo.get_pipeline(pipeline_id)
        if not pipeline:
            raise NotFoundError("Pipeline", pipeline_id)
        return pipeline

    def list_pipelines(self) -> List[Pipeline]:
        return self.repo.list_pipelines()

    def update_pipeline(self, pipeline_id: str, payload: PipelineUpdate) -> Pipeline:
        pipeline = self.get_pipeline(pipeline_id)
        data = payload.model_dump(exclude_unset=True)

        if data.get("is_default"):
            self._clear_default_flag()

        return self.repo.update_pipeline(pipeline, data)

    def delete_pipeline(self, pipeline_id: str) -> None:
        pipeline = self.get_pipeline(pipeline_id)

        # Prevent deleting the only active pipeline
        all_pipelines = self.repo.list_pipelines()
        active = [p for p in all_pipelines if p.is_active and p.id != pipeline_id]
        if not active:
            raise BusinessRuleError(
                "Cannot delete the last active pipeline. Create a new pipeline first."
            )

        self.repo.deactivate_pipeline(pipeline)
        log.info("pipeline.deleted", pipeline_id=pipeline_id)

    def _clear_default_flag(self) -> None:
        """Remove the default flag from any currently-default pipeline."""
        for p in self.repo.list_pipelines():
            if p.is_default:
                self.repo.update_pipeline(p, {"is_default": False})

    # ------------------------------------------------------------------
    # Stage CRUD
    # ------------------------------------------------------------------

    def create_stage(self, pipeline_id: str, payload: StageCreate) -> PipelineStage:
        self.get_pipeline(pipeline_id)  # raises if not found / not in workspace
        data = payload.model_dump(exclude_unset=False)
        data["pipeline_id"] = pipeline_id
        stage = self.repo.create_stage(data)
        log.info("stage.created", pipeline_id=pipeline_id, stage_id=stage.id)
        return stage

    def get_stage(self, stage_id: str) -> PipelineStage:
        stage = self.repo.get_stage(stage_id)
        if not stage:
            raise NotFoundError("PipelineStage", stage_id)
        return stage

    def list_stages(self, pipeline_id: str) -> List[PipelineStage]:
        self.get_pipeline(pipeline_id)
        return self.repo.list_stages(pipeline_id)

    def update_stage(self, stage_id: str, payload: StageUpdate) -> PipelineStage:
        stage = self.get_stage(stage_id)
        data = payload.model_dump(exclude_unset=True)
        return self.repo.update_stage(stage, data)

    def delete_stage(self, stage_id: str) -> None:
        stage = self.get_stage(stage_id)
        self.repo.delete_stage(stage)
        log.info("stage.deleted", stage_id=stage_id)

    # ------------------------------------------------------------------
    # Kanban board
    # ------------------------------------------------------------------

    def get_board(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Return the full Kanban board with stages and their deals.
        Returns a single well-structured dict for the frontend.
        """
        pipeline = self.get_pipeline(pipeline_id)
        stages = self.repo.list_stages(pipeline_id)
        board = self.repo.get_board(pipeline_id)

        from app.schemas.deal import DealResponse

        columns = []
        for stage in stages:
            deals = board.get(stage.id, [])
            deal_dicts = []
            for d in deals:
                try:
                    deal_dicts.append(DealResponse.model_validate(d).model_dump())
                except Exception:
                    pass
            columns.append({
                "stage_id": stage.id,
                "stage_name": stage.name,
                "color": stage.color,
                "order": stage.order,
                "is_won_stage": stage.is_won_stage,
                "is_lost_stage": stage.is_lost_stage,
                "deal_count": len(deal_dicts),
                "total_value": sum(d["value"] for d in deal_dicts),
                "deals": deal_dicts,
            })

        return {
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline.name,
            "columns": columns,
        }

    def move_deal(self, deal_id: str, stage_id: str, position: int = 0) -> None:
        """Move a deal to a different stage on the Kanban board."""
        stage = self.get_stage(stage_id)
        pipeline_id = stage.pipeline_id

        mapping = self.repo.get_mapping(deal_id, pipeline_id)
        if not mapping:
            # Auto-map deal to pipeline if not yet mapped
            self.repo.map_deal(deal_id, pipeline_id, stage_id, position)
        else:
            self.repo.move_deal(mapping, stage_id, position)

        log.info("kanban.deal_moved", deal_id=deal_id, stage_id=stage_id)
