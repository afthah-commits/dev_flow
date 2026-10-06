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
    # Phase 36 types
    DAILY_REPORT_REMINDER = "DAILY_REPORT_REMINDER"
    DAILY_REPORT_BLOCKER = "DAILY_REPORT_BLOCKER"
    RELEASE_APPROVAL_REQUESTED = "RELEASE_APPROVAL_REQUESTED"
    RELEASE_APPROVED = "RELEASE_APPROVED"
    RELEASE_REJECTED = "RELEASE_REJECTED"
    RELEASE_PROMOTED = "RELEASE_PROMOTED"
    RELEASE_ROLLBACK = "RELEASE_ROLLBACK"
    DEPLOYMENT_STARTED = "DEPLOYMENT_STARTED"
    DEPLOYMENT_SUCCESS = "DEPLOYMENT_SUCCESS"
    DEPLOYMENT_FAILED = "DEPLOYMENT_FAILED"
    DEPLOYMENT_ROLLBACK = "DEPLOYMENT_ROLLBACK"
    JOB_FAILURE = "JOB_FAILURE"
    AUTOMATION_FAILURE = "AUTOMATION_FAILURE"
    WORKFLOW_APPROVAL_REQUESTED = "WORKFLOW_APPROVAL_REQUESTED"
    WORKFLOW_APPROVED = "WORKFLOW_APPROVED"
    WORKFLOW_REJECTED = "WORKFLOW_REJECTED"
    CLIENT_REQUEST_CREATED = "CLIENT_REQUEST_CREATED"
    CLIENT_REQUEST_UPDATED = "CLIENT_REQUEST_UPDATED"
    TEAM_ACTIVITY = "TEAM_ACTIVITY"

class NotificationPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(String, nullable=False, index=True)
    priority = Column(String, default="NORMAL", nullable=False)
    entity_type = Column(String, nullable=True, index=True)
    entity_id = Column(Uuid, nullable=True, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, nullable=False, index=True)
    action_required = Column(Boolean, default=False, nullable=False, index=True)
    important = Column(Boolean, default=False, nullable=False, index=True)
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
    daily_report_notifications = Column(Boolean, default=True, nullable=False)
    deployment_notifications = Column(Boolean, default=True, nullable=False)
    release_notifications = Column(Boolean, default=True, nullable=False)
    job_notifications = Column(Boolean, default=True, nullable=False)
    automation_notifications = Column(Boolean, default=True, nullable=False)
    workflow_approval_notifications = Column(Boolean, default=True, nullable=False)
    client_request_notifications = Column(Boolean, default=True, nullable=False)
    team_activity_notifications = Column(Boolean, default=True, nullable=False)
    digest_notifications = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="notification_preferences")
