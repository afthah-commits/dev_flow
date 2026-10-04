from typing import Any, Dict, Callable
from sqlalchemy.orm import Session
import asyncio

class EventBus:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, callback: Callable):
        self.subscribers.append(callback)

    async def publish(self, db: Session, event_type: str, organization_id: str, entity_type: str, entity_id: str, payload: Dict[str, Any]):
        full_payload = {
            "event_type": event_type,
            "organization_id": organization_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload": payload,
            "timestamp": "now" # In real app, standard ISO format
        }
        for sub in self.subscribers:
            try:
                # Some might be async, some sync. For simplicity assume async
                await sub(db, full_payload)
            except Exception as e:
                print(f"EventBus subscriber error: {e}")

event_bus = EventBus()
