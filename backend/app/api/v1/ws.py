from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.api import deps
from app.websockets.manager import manager
from app.models.organization import OrganizationMember

router = APIRouter()

# Note: WebSocket endpoints usually handle authentication via token in query params because browser WS API doesn't support custom headers easily.

@router.websocket("")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    org_id: UUID = Query(...)
):
    # In a real app we would properly decode the JWT here
    # For now, we mock the auth or use a simplistic dependency
    db = next(deps.get_db())
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        user_id = UUID(payload.get("sub"))
        
        # Verify org membership
        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id
        ).first()
        if not member:
            await websocket.close(code=1008)
            return

        await manager.connect(websocket, org_id, user_id)
        
        # Broadcast presence
        await manager.broadcast_to_org(org_id, {
            "type": "USER_PRESENCE_CHANGED",
            "user_id": str(user_id),
            "status": "ONLINE"
        })

        try:
            while True:
                data = await websocket.receive_text()
                # Handle incoming messages if needed
        except WebSocketDisconnect:
            manager.disconnect(websocket, org_id, user_id)
            await manager.broadcast_to_org(org_id, {
                "type": "USER_PRESENCE_CHANGED",
                "user_id": str(user_id),
                "status": "OFFLINE"
            })
    except Exception as e:
        await websocket.close(code=1008)
