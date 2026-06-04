from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError

from app.core.logging import get_logger
from app.core.security import decode_token
from app.websocket.manager import manager

router = APIRouter(tags=["WebSocket"])
logger = get_logger(__name__)


async def _authenticate_ws(token: Optional[str]) -> Optional[tuple[str, str]]:
    """Validate JWT and return (user_id, org_id) or None."""
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        org_id = payload.get("org_id")
        if not user_id or not org_id:
            return None
        return user_id, org_id
    except JWTError:
        return None


@router.websocket("/ws/dashboard/{dashboard_id}")
async def dashboard_ws(
    websocket: WebSocket,
    dashboard_id: str,
    token: Optional[str] = Query(None),
):
    auth = await _authenticate_ws(token)
    if not auth:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id, org_id = auth
    await manager.connect(websocket, org_id, user_id)

    try:
        await websocket.send_json({"type": "connected", "dashboard_id": dashboard_id})
        while True:
            # Keep the connection alive; server pushes updates
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(org_id, user_id)
    except Exception as e:
        logger.error("ws_error", error=str(e))
        manager.disconnect(org_id, user_id)


@router.websocket("/ws/events/stream")
async def event_stream_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    auth = await _authenticate_ws(token)
    if not auth:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id, org_id = auth
    # Use a dedicated stream key for event tailing
    stream_key = f"stream:{user_id}"
    await manager.connect(websocket, org_id, user_id)

    try:
        await websocket.send_json({"type": "stream_started"})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(org_id, user_id)
    except Exception as e:
        logger.error("ws_stream_error", error=str(e))
        manager.disconnect(org_id, user_id)


@router.websocket("/ws/alerts")
async def alerts_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    auth = await _authenticate_ws(token)
    if not auth:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id, org_id = auth
    await manager.connect(websocket, org_id, user_id)

    try:
        await websocket.send_json({"type": "alerts_connected"})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(org_id, user_id)
    except Exception as e:
        logger.error("ws_alerts_error", error=str(e))
        manager.disconnect(org_id, user_id)
