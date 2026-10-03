from abc import ABC, abstractmethod
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.notification import Notification

class NotificationChannel(ABC):
    @abstractmethod
    def send(self, db: Session, user_id: UUID, notification_data: Dict[str, Any]) -> None:
        pass

class InAppNotificationChannel(NotificationChannel):
    def send(self, db: Session, user_id: UUID, notification_data: Dict[str, Any]) -> None:
        n = Notification(
            user_id=user_id,
            project_id=notification_data.get("project_id"),
            type=notification_data.get("type", "SYSTEM"),
            title=notification_data.get("title", ""),
            message=notification_data.get("message", ""),
            priority=notification_data.get("priority", "NORMAL"),
            entity_type=notification_data.get("entity_type"),
            entity_id=notification_data.get("entity_id")
        )
        db.add(n)
        db.commit()

class EmailNotificationChannel(NotificationChannel):
    def send(self, db: Session, user_id: UUID, notification_data: Dict[str, Any]) -> None:
        # Placeholder for actual email sending logic
        # user = db.query(User).filter(User.id == user_id).first()
        # send_email(to=user.email, subject=notification_data["title"], body=notification_data["message"])
        print(f"[EMAIL MOCK] Sending email to User {user_id}: {notification_data.get('title')} - {notification_data.get('message')}")
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
