from abc import ABC, abstractmethod
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from uuid import UUID
import asyncio

from app.models.notification import Notification


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, db: Session, user_id: UUID, notification_data: Dict[str, Any]) -> None:
        pass


class InAppNotificationChannel(NotificationChannel):
    def send(self, db: Session, user_id: UUID, notification_data: Dict[str, Any]) -> None:
        n = Notification(
            user_id=user_id,
            organization_id=notification_data.get("organization_id"),
            project_id=notification_data.get("project_id"),
            type=notification_data.get("type", "SYSTEM"),
            title=notification_data.get("title", ""),
            message=notification_data.get("message", ""),
            priority=notification_data.get("priority", "NORMAL"),
            entity_type=notification_data.get("entity_type"),
            entity_id=notification_data.get("entity_id"),
            action_required=notification_data.get("action_required", False),
            important=notification_data.get("important", False),
        )
        db.add(n)
        db.commit()
        db.refresh(n)

        # Phase 36: Broadcast via WebSocket to the user
        try:
            from app.websockets.manager import manager
            payload = {
                "type": "notification.created",
                "notification_id": str(n.id),
                "title": n.title,
                "notification_type": n.type,
                "priority": n.priority,
                "read": False,
                "action_required": bool(n.action_required),
                "important": bool(n.important),
            }
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(manager.send_personal_message(payload, user_id))
                # Action Center also listens for action_item.* on the org scope
                if n.action_required and n.organization_id:
                    asyncio.ensure_future(manager.broadcast_to_org(n.organization_id, {
                        "type": "action_item.created",
                        "notification_id": str(n.id),
                        "user_id": str(user_id),
                        "entity_type": n.entity_type,
                        "entity_id": str(n.entity_id) if n.entity_id else None,
                    }))
            else:
                loop.run_until_complete(manager.send_personal_message(payload, user_id))
                if n.action_required and n.organization_id:
                    loop.run_until_complete(manager.broadcast_to_org(n.organization_id, {
                        "type": "action_item.created",
                        "notification_id": str(n.id),
                        "user_id": str(user_id),
                        "entity_type": n.entity_type,
                        "entity_id": str(n.entity_id) if n.entity_id else None,
                    }))
        except Exception:
            pass


class EmailNotificationChannel(NotificationChannel):
    def send(self, db: Session, user_id: UUID, notification_data: Dict[str, Any]) -> None:
        # Placeholder for actual email sending logic
        pass


class NotificationDispatcher:
    def __init__(self):
        self.channels: List[NotificationChannel] = [
            InAppNotificationChannel(),
            EmailNotificationChannel()
        ]

    def dispatch(self, db: Session, user_id: UUID, notification_data: Dict[str, Any]):
        for channel in self.channels:
            try:
                channel.send(db, user_id, notification_data)
            except Exception as e:
                print(f"Failed to send notification via {channel.__class__.__name__}: {e}")


dispatcher = NotificationDispatcher()
