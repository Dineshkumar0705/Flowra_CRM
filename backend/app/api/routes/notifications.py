"""
Notification routes — list, mark read, activity log, and real-time WebSocket feed.

WebSocket:
  ws://localhost:8000/api/v1/notifications/ws?token=<access_token>

  The client connects once and receives push messages whenever a new
  Notification is created for the authenticated user. Format:

    { "type": "notification", "data": { "id", "title", "body", "action_url" } }
    { "type": "ping" }   ← server keepalive every 30s
"""

import asyncio
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.deps import CurrentUserDep, DbDep, PaginationDep, WorkspaceIdDep, WorkspaceMemberDep
from app.core.websocket_manager import ws_manager
from app.schemas.base import PaginatedResponse, SuccessResponse, paginated, success
from app.schemas.notification import ActivityLogResponse, MarkReadRequest, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter()
log = logging.getLogger("flowra.route.notifications")

# Expose manager for use in notification_tasks.py
manager = ws_manager


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[NotificationResponse])
def list_notifications(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    pagination: PaginationDep,
    unread_only: bool = Query(False),
):
    """List notifications for the current user."""
    svc = NotificationService(db, workspace_id)
    items, total = svc.list_for_user(
        user_id=current_user.id,
        unread_only=unread_only,
        skip=pagination.skip,
        per_page=pagination.limit,
    )
    return paginated(
        [NotificationResponse.model_validate(n) for n in items],
        total=total,
        page=pagination.page,
        per_page=pagination.limit,
    )


@router.get("/unread-count", response_model=SuccessResponse[dict])
def unread_count(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return the number of unread notifications for the current user."""
    svc = NotificationService(db, workspace_id)
    count = svc.unread_count(current_user.id)
    return success({"unread_count": count})


@router.post("/mark-read", response_model=SuccessResponse[dict])
def mark_read(
    payload: MarkReadRequest,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Mark specific notification IDs as read."""
    svc = NotificationService(db, workspace_id)
    updated = svc.mark_read(current_user.id, payload.notification_ids)
    return success({"updated": updated}, message=f"{updated} notification(s) marked as read.")


@router.post("/mark-all-read", response_model=SuccessResponse[dict])
def mark_all_read(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Mark all unread notifications as read."""
    svc = NotificationService(db, workspace_id)
    updated = svc.mark_all_read(current_user.id)
    return success({"updated": updated}, message=f"All {updated} notification(s) marked as read.")


# ---------------------------------------------------------------------------
# Activity log (audit trail)
# ---------------------------------------------------------------------------


@router.get("/activity", response_model=PaginatedResponse[ActivityLogResponse])
def get_activity_log(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    pagination: PaginationDep,
    entity_type: Optional[str] = Query(None, description="e.g. deal, contact"),
    entity_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
):
    """Return the audit activity log with optional filters."""
    svc = NotificationService(db, workspace_id)
    items, total = svc.get_activity_log(
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        skip=pagination.skip,
        per_page=pagination.limit,
    )
    return paginated(
        [ActivityLogResponse.model_validate(e) for e in items],
        total=total,
        page=pagination.page,
        per_page=pagination.limit,
    )


# ---------------------------------------------------------------------------
# WebSocket — real-time notification stream
# ---------------------------------------------------------------------------


@router.websocket("/ws")
async def notifications_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="Valid access token"),
):
    """
    Real-time notification WebSocket endpoint.

    Connect: ws://localhost:8000/api/v1/notifications/ws?token=<access_token>

    Server → client messages:
      { "type": "notification", "data": { "id", "title", "body", "action_url" } }
      { "type": "ping" }

    Client → server messages:
      { "type": "pong" }   ← keepalive reply (optional)
      { "type": "mark_read", "notification_ids": ["id1", "id2"] }
    """
    # Authenticate
    try:
        user_id = await ws_manager.authenticate(websocket, token)
    except Exception:
        return   # socket already closed by authenticate()

    await ws_manager.connect(user_id, websocket)
    log.info("ws.notification_stream_open", user_id=user_id)

    # Send initial unread count so the client can sync immediately
    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "data": {"user_id": user_id, "message": "Notification stream active."},
        }))
    except Exception:
        ws_manager.disconnect(user_id, websocket)
        return

    # Keep-alive loop — send ping every 25 seconds, process client messages
    try:
        ping_interval = 25  # seconds
        elapsed = 0
        while True:
            # Non-blocking receive with 1-second timeout
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                msg = json.loads(raw)

                if msg.get("type") == "pong":
                    pass   # Client replied to our ping — connection is alive

                elif msg.get("type") == "mark_read":
                    # Allow client to mark notifications read from WS
                    ids = msg.get("notification_ids", [])
                    if ids:
                        # Fire-and-forget DB update — don't block the WS loop
                        asyncio.create_task(_mark_read_task(user_id, ids))

            except asyncio.TimeoutError:
                elapsed += 1
                if elapsed >= ping_interval:
                    elapsed = 0
                    await websocket.send_text(json.dumps({"type": "ping"}))

    except WebSocketDisconnect:
        log.info("ws.notification_stream_closed", user_id=user_id)
    except Exception as exc:
        log.error("ws.notification_stream_error", user_id=user_id, error=str(exc))
    finally:
        ws_manager.disconnect(user_id, websocket)


async def _mark_read_task(user_id: str, notification_ids: List[str]) -> None:
    """Async helper to mark notifications read without blocking WS loop."""
    import asyncio
    from app.core.database import SessionLocal
    from app.models.notification import Notification
    from datetime import datetime, timezone

    def _db_update():
        db = SessionLocal()
        try:
            db.query(Notification).filter(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            ).update({"read_at": datetime.now(timezone.utc)}, synchronize_session=False)
            db.commit()
        finally:
            db.close()

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _db_update)
