from __future__ import annotations

from typing import Any, Dict, Optional, Set
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections grouped by organization.
    Supports broadcasting to all org members and direct user messages.
    """

    def __init__(self) -> None:
        # org_id -> {user_id -> websocket}
        self._connections: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: Any, org_id: str, user_id: str) -> None:
        await websocket.accept()
        if org_id not in self._connections:
            self._connections[org_id] = {}
        self._connections[org_id][user_id] = websocket
        logger.info("ws_connected", org_id=org_id, user_id=user_id)

    def disconnect(self, org_id: str, user_id: str) -> None:
        org_clients = self._connections.get(org_id, {})
        org_clients.pop(user_id, None)
        if not org_clients:
            self._connections.pop(org_id, None)
        logger.info("ws_disconnected", org_id=org_id, user_id=user_id)

    async def send_to_user(
        self, org_id: str, user_id: str, message: Dict[str, Any]
    ) -> None:
        ws = self._connections.get(org_id, {}).get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning("ws_send_failed", user_id=user_id, error=str(e))
                self.disconnect(org_id, user_id)

    async def broadcast_to_org(self, org_id: str, message: Dict[str, Any]) -> None:
        clients = dict(self._connections.get(org_id, {}))
        for user_id, ws in clients.items():
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning("ws_broadcast_failed", user_id=user_id, error=str(e))
                self.disconnect(org_id, user_id)

    def get_connected_user_ids(self, org_id: str) -> Set[str]:
        return set(self._connections.get(org_id, {}).keys())

    @property
    def total_connections(self) -> int:
        return sum(len(clients) for clients in self._connections.values())


# Global singleton
manager = ConnectionManager()
