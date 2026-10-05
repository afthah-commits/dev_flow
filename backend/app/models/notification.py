import uuid
import enum
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class NotificationType:
    TASK_OVERDUE = "TASK_OVERDUE"
    TASK_DUE_SOON = "TASK_DUE_SOON"
    PROJECT_DEADLINE = "PROJECT_DEADLINE"
    PROJECT_AT_RISK = "PROJECT_AT_RISK"
    GITHUB_PR = "GITHUB_PR"
    GITHUB_ISSUE = "GITHUB_ISSUE"
    GITHUB_ACTIVITY = "GITHUB_ACTIVITY"
    AI_INSIGHT = "AI_INSIGHT"

class NotificationPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(String, nullable=False, index=True)
    priority = Column(String, default="NORMAL", nullable=False)
    entity_type = Column(String, nullable=True, index=True)
    entity_id = Column(Uuid, nullable=True, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="notifications")
    project = relationship("Project")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    task_notifications = Column(Boolean, default=True, nullable=False)
    task_assignments = Column(Boolean, default=True, nullable=False)
    deadline_notifications = Column(Boolean, default=True, nullable=False)
    project_health_notifications = Column(Boolean, default=True, nullable=False)
    github_notifications = Column(Boolean, default=True, nullable=False)
    ai_notifications = Column(Boolean, default=True, nullable=False)
    sprint_events = Column(Boolean, default=True, nullable=False)
    milestone_events = Column(Boolean, default=True, nullable=False)
    security_events = Column(Boolean, default=True, nullable=False)
    digest_notifications = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="notification_preferences")
