from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class NotificationBase(BaseModel):
    organization_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    type: str
    priority: str = "NORMAL"
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    title: str
    message: str
    read: bool = False
    action_required: bool = False
    important: bool = False


class NotificationResponse(NotificationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationPreferenceBase(BaseModel):
    task_notifications: bool = True
    task_assignments: bool = True
    deadline_notifications: bool = True
    project_health_notifications: bool = True
    github_notifications: bool = True
    ai_notifications: bool = True
    sprint_events: bool = True
    milestone_events: bool = True
    security_events: bool = True
    digest_notifications: bool = False
    daily_report_notifications: bool = True
    deployment_notifications: bool = True
    release_notifications: bool = True
    job_notifications: bool = True
    automation_notifications: bool = True
    workflow_approval_notifications: bool = True
    client_request_notifications: bool = True
    team_activity_notifications: bool = True


class NotificationPreferenceResponse(NotificationPreferenceBase):
    user_id: UUID
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    count: int


class NotificationSummary(BaseModel):
    unread: int
    important: int
    action_required: int
    pending_approvals: int
    failed_jobs: int


class ActionItemResponse(BaseModel):
    id: str
    type: str
    title: str
    description: str
    entity_type: str
    entity_id: Optional[str] = None
    priority: str = "NORMAL"
    created_at: datetime
    action_url: Optional[str] = None
