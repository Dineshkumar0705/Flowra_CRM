"""
Generic base repository.

Provides create / get / list / update / soft_delete operations that every
model-specific repository can inherit and extend.

All queries automatically filter on workspace_id (multi-tenancy) and
deleted_at IS NULL (soft-delete) unless explicitly opted out.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import Base

log = logging.getLogger("flowra.repo")

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic CRUD repository.

    Args:
        model:      The SQLAlchemy model class.
        db:         Active database session.
        workspace_id: Current tenant — every query is scoped to this value.
    """

    def __init__(self, model: Type[ModelT], db: Session, workspace_id: str) -> None:
        self.model = model
        self.db = db
        self.workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Base query helpers
    # ------------------------------------------------------------------

    def _base_q(self):
        """Return a query scoped to the current workspace, excluding soft-deleted rows."""
        q = self.db.query(self.model).filter(
            self.model.workspace_id == self.workspace_id  # type: ignore[attr-defined]
        )
        if hasattr(self.model, "deleted_at"):
            q = q.filter(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        return q

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, data: Dict[str, Any]) -> ModelT:
        """
        Insert a new row.

        Args:
            data: Column values as a dict.  workspace_id is injected automatically.

        Returns:
            The persisted model instance (refreshed from DB).
        """
        data.setdefault("workspace_id", self.workspace_id)
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        log.debug("repo.create", model=self.model.__name__, id=instance.id)
        return instance

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, record_id: str) -> Optional[ModelT]:
        """
        Fetch a single row by primary key, scoped to current workspace.

        Returns:
            Model instance or None if not found / already deleted.
        """
        return self._base_q().filter(self.model.id == record_id).first()  # type: ignore[attr-defined]

    def get_or_raise(self, record_id: str, resource_name: str = "Resource") -> ModelT:
        """
        Fetch by ID or raise NotFoundError.

        Raises:
            NotFoundError: If the record does not exist.
        """
        from app.core.exceptions import NotFoundError

        record = self.get_by_id(record_id)
        if record is None:
            raise NotFoundError(resource_name, record_id)
        return record

    # ------------------------------------------------------------------
    # List with pagination
    # ------------------------------------------------------------------

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        order_by_column: Optional[str] = "created_at",
        order_desc: bool = True,
    ) -> Tuple[List[ModelT], int]:
        """
        Return a page of records and the total count.

        Args:
            skip:            Number of rows to skip.
            limit:           Maximum rows to return.
            order_by_column: Column name to sort by.
            order_desc:      True for descending, False for ascending.

        Returns:
            Tuple (items, total_count).
        """
        q = self._base_q()
        total: int = q.count()

        if order_by_column and hasattr(self.model, order_by_column):
            col = getattr(self.model, order_by_column)
            q = q.order_by(col.desc() if order_desc else col.asc())

        items = q.offset(skip).limit(limit).all()
        return items, total

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, instance: ModelT, data: Dict[str, Any]) -> ModelT:
        """
        Apply a partial update to an existing row.

        Args:
            instance: The model instance to update.
            data:     Dict of column → new value pairs.

        Returns:
            The updated instance (refreshed from DB).
        """
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]

        self.db.commit()
        self.db.refresh(instance)
        return instance

    # ------------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------------

    def soft_delete(self, instance: ModelT) -> None:
        """
        Soft-delete a row by setting deleted_at.

        The row remains in the database but is excluded from all
        _base_q() queries.
        """
        if hasattr(instance, "soft_delete"):
            instance.soft_delete()  # type: ignore[attr-defined]
        elif hasattr(instance, "deleted_at"):
            instance.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        self.db.commit()
        log.info("repo.soft_delete", model=self.model.__name__, id=instance.id)

    # ------------------------------------------------------------------
    # Hard delete (use sparingly)
    # ------------------------------------------------------------------

    def hard_delete(self, instance: ModelT) -> None:
        """Permanently remove a row from the database."""
        self.db.delete(instance)
        self.db.commit()

    # ------------------------------------------------------------------
    # Exists
    # ------------------------------------------------------------------

    def exists(self, record_id: str) -> bool:
        return self._base_q().filter(self.model.id == record_id).count() > 0  # type: ignore[attr-defined]
