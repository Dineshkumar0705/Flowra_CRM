"""Workspace and WorkspaceMember repository."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.workspace import MemberRole, Workspace, WorkspaceMember

log = logging.getLogger("flowra.repo.workspace")


class WorkspaceRepository:
    """CRUD for Workspace and WorkspaceMember tables."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Workspace
    # ------------------------------------------------------------------

    def create(self, data: dict) -> Workspace:
        ws = Workspace(**data)
        self.db.add(ws)
        self.db.commit()
        self.db.refresh(ws)
        return ws

    def get_by_id(self, workspace_id: str) -> Optional[Workspace]:
        return (
            self.db.query(Workspace)
            .filter(Workspace.id == workspace_id, Workspace.deleted_at.is_(None))
            .first()
        )

    def get_by_slug(self, slug: str) -> Optional[Workspace]:
        return (
            self.db.query(Workspace)
            .filter(Workspace.slug == slug, Workspace.deleted_at.is_(None))
            .first()
        )

    def slug_exists(self, slug: str) -> bool:
        return (
            self.db.query(Workspace.id)
            .filter(Workspace.slug == slug)
            .first()
        ) is not None

    def update(self, ws: Workspace, data: dict) -> Workspace:
        from datetime import datetime, timezone
        for k, v in data.items():
            if hasattr(ws, k):
                setattr(ws, k, v)
        ws.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(ws)
        return ws

    def list_for_user(self, user_id: str) -> List[Workspace]:
        """Return all active workspaces the user is a member of."""
        return (
            self.db.query(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.is_active == True,
                Workspace.deleted_at.is_(None),
                Workspace.is_active == True,
            )
            .all()
        )

    def soft_delete(self, ws: Workspace) -> None:
        ws.soft_delete()
        self.db.commit()

    # ------------------------------------------------------------------
    # WorkspaceMember
    # ------------------------------------------------------------------

    def add_member(self, workspace_id: str, user_id: str, role: MemberRole) -> WorkspaceMember:
        member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_member(self, workspace_id: str, user_id: str) -> Optional[WorkspaceMember]:
        return (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .first()
        )

    def list_members(self, workspace_id: str) -> List[WorkspaceMember]:
        return (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.is_active == True,
            )
            .all()
        )

    def update_member_role(self, member: WorkspaceMember, role: MemberRole) -> WorkspaceMember:
        member.role = role
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, member: WorkspaceMember) -> None:
        member.is_active = False
        self.db.commit()
