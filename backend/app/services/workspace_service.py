"""Workspace management service."""

import logging
from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.workspace import MemberRole, Workspace, WorkspaceMember
from app.repositories.workspace_repo import WorkspaceRepository
from app.schemas.workspace import AddMemberRequest, UpdateWorkspaceRequest

log = logging.getLogger("flowra.service.workspace")


class WorkspaceService:
    """Handles workspace CRUD and member management."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = WorkspaceRepository(db)

    # ------------------------------------------------------------------
    # Workspace
    # ------------------------------------------------------------------

    def get_or_raise(self, workspace_id: str) -> Workspace:
        ws = self.repo.get_by_id(workspace_id)
        if not ws:
            raise NotFoundError("Workspace", workspace_id)
        return ws

    def list_for_user(self, user_id: str) -> List[Workspace]:
        return self.repo.list_for_user(user_id)

    def update(self, workspace_id: str, payload: UpdateWorkspaceRequest) -> Workspace:
        ws = self.get_or_raise(workspace_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return ws
        return self.repo.update(ws, updates)

    # ------------------------------------------------------------------
    # Members
    # ------------------------------------------------------------------

    def list_members(self, workspace_id: str) -> List[WorkspaceMember]:
        return self.repo.list_members(workspace_id)

    def add_member(self, workspace_id: str, payload: AddMemberRequest) -> WorkspaceMember:
        """
        Add a user to the workspace by email.
        Raises ConflictError if already a member.
        Raises NotFoundError if the user doesn't exist.
        """
        from app.repositories.user_repo import UserRepository
        user_repo = UserRepository(self.db)
        user = user_repo.get_by_email(payload.email)
        if not user:
            raise NotFoundError("User", payload.email)

        # Check for existing membership
        existing = self.repo.get_member(workspace_id, user.id)
        if existing:
            raise ConflictError(f"User {payload.email} is already a member of this workspace.")

        member = self.repo.add_member(workspace_id, user.id, role=payload.role)
        log.info("workspace.member_added", workspace_id=workspace_id, user_id=user.id, role=str(payload.role))
        return member

    def update_member_role(self, workspace_id: str, user_id: str, role: MemberRole) -> WorkspaceMember:
        member = self.repo.get_member(workspace_id, user_id)
        if not member:
            raise NotFoundError("WorkspaceMember", user_id)
        # update_member_role in workspace_repo takes (member, role)
        return self.repo.update_member_role(member, role)

    def remove_member(self, workspace_id: str, user_id: str) -> None:
        member = self.repo.get_member(workspace_id, user_id)
        if not member:
            raise NotFoundError("WorkspaceMember", user_id)
        # Prevent removing the owner
        role_val = member.role.value if hasattr(member.role, "value") else str(member.role)
        if role_val == "owner":
            raise BusinessRuleError("Cannot remove the workspace owner.")
        # remove_member in workspace_repo takes (member,)
        self.repo.remove_member(member)
        log.info("workspace.member_removed", workspace_id=workspace_id, user_id=user_id)
