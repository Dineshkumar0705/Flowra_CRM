"""
WebSocket connection manager — handles real-time notification delivery.

Each authenticated user can have multiple WebSocket connections open
(multiple browser tabs). Messages are broadcast to all active connections
for a given user_id.

Usage in routes:
    from app.core.websocket_manager import ws_manager

    @router.websocket("/ws")
    async def notifications_ws(websocket: WebSocket, token: str):
        user_id = await ws_manager.authenticate(websocket, token)
        await ws_manager.connect(user_id, websocket)
        try:
            while True:
                await websocket.receive_text()   # keep alive / ping-pong
        except WebSocketDisconnect:
            ws_manager.disconnect(user_id, websocket)
"""

import json
import logging
from collections import defaultdict
from typing import Any, Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.core.exceptions import UnauthorizedError

log = logging.getLogger("flowra.websocket")


class ConnectionManager:
    """
    In-process WebSocket connection registry.

    For multi-process deployments (multiple uvicorn workers), replace the
    in-memory dict with a Redis pub/sub channel so all workers share state.
    The `broadcast_via_redis()` method below is the hook for that upgrade.
    """

    def __init__(self) -> None:
        # user_id → set of active WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def authenticate(self, websocket: WebSocket, token: str) -> str:
        """
        Validate the JWT token provided as a query param.
        Returns user_id on success; closes the socket on failure.
        """
        from app.core.security import decode_token

        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            token_type = payload.get("type")
            if not user_id or token_type != "access":
                raise ValueError("Invalid token")
            return str(user_id)
        except Exception:
            await websocket.close(code=4001, reason="Invalid token")
            raise UnauthorizedError("WebSocket authentication failed.")

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Accept the WebSocket and register it."""
        await websocket.accept()
        self._connections[user_id].add(websocket)
        connection_count = len(self._connections[user_id])
        log.info("ws.connected", user_id=user_id, total_connections=connection_count)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Remove a closed WebSocket connection."""
        self._connections[user_id].discard(websocket)
        if not self._connections[user_id]:
            del self._connections[user_id]
        log.info("ws.disconnected", user_id=user_id)

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        Send a JSON message to all active connections for user_id.
        Returns the number of connections that received the message.
        Dead connections are cleaned up automatically.
        """
        connections = list(self._connections.get(user_id, set()))
        if not connections:
            return 0

        payload = json.dumps(message)
        dead: List[WebSocket] = []
        sent = 0

        for ws in connections:
            try:
                await ws.send_text(payload)
                sent += 1
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            self._connections[user_id].discard(ws)

        return sent

    async def broadcast_to_workspace(
        self, workspace_id: str, user_ids: List[str], message: Dict[str, Any]
    ) -> int:
        """Send a message to all online users in a workspace."""
        total = 0
        for user_id in user_ids:
            total += await self.send_to_user(user_id, message)
        return total

    def is_online(self, user_id: str) -> bool:
        """Check if a user has at least one active WebSocket connection."""
        return bool(self._connections.get(user_id))

    def online_users(self) -> List[str]:
        """Return list of user IDs with active connections."""
        return list(self._connections.keys())

    # ------------------------------------------------------------------
    # Redis pub/sub hook (for multi-worker production deployments)
    # ------------------------------------------------------------------

    async def broadcast_via_redis(self, user_id: str, message: Dict[str, Any]) -> None:
        """
        Publish a message to a Redis channel that all workers subscribe to.
        Each worker checks if the target user is connected locally and delivers.

        Upgrade path:
          1. Install `redis[asyncio]`
          2. Subscribe to "ws:notifications" channel in lifespan
          3. Replace `send_to_user()` calls with this method
        """
        # Placeholder — implement with aioredis when scaling to multiple workers
        await self.send_to_user(user_id, message)


# Global singleton — imported by routes and tasks
ws_manager = ConnectionManager()
