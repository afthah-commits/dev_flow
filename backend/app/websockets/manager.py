from typing import List, Dict, Optional
from uuid import UUID
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # A dictionary mapping organization ID to a list of active websocket connections
        self.active_connections: Dict[UUID, List[WebSocket]] = {}
        # Mapping user ID to websocket for direct messages
        self.user_connections: Dict[UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket, org_id: UUID, user_id: UUID):
        await websocket.accept()
        if org_id not in self.active_connections:
            self.active_connections[org_id] = []
        self.active_connections[org_id].append(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, org_id: UUID, user_id: UUID):
        if org_id in self.active_connections:
            if websocket in self.active_connections[org_id]:
                self.active_connections[org_id].remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]

    async def broadcast_to_org(self, org_id: UUID, message: dict):
        if org_id in self.active_connections:
            for connection in self.active_connections[org_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def send_personal_message(self, message: dict, user_id: UUID):
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
