from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from uuid import UUID
import logging
from app.api import deps
from app.websockets.manager import manager
from app.models.organization import OrganizationMember

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def realtime_ws(
    websocket: WebSocket,
    token: str = Query(...),
    org_id: UUID = Query(...),
    db: Session = Depends(deps.get_db),
):
    # Phase 31: use the injected session (dependency overrides + guaranteed
    # close) instead of a hand-rolled session that was never closed.
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        user_id = UUID(payload.get("sub"))
        
        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id
        ).first()
        if not member:
            await websocket.close(code=1008)
            return

        await manager.connect(websocket, org_id, user_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                # could process incoming events from client here
        except WebSocketDisconnect:
            manager.disconnect(websocket, org_id, user_id)
    except WebSocketDisconnect:
        raise
    except Exception as e:
        # Log the exception TYPE only — never the message or token.
        logger.warning("Realtime WS connection rejected: %s", type(e).__name__)
        await websocket.close(code=1008)
