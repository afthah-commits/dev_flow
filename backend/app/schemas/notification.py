from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class NotificationBase(BaseModel):
    project_id: Optional[UUID] = None
    type: str
    priority: str = "NORMAL"
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    title: str
    message: str
    read: bool = False

class NotificationResponse(NotificationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class NotificationPreferenceBase(BaseModel):
    task_notifications: bool
    task_assignments: bool = True
    deadline_notifications: bool
    project_health_notifications: bool
    github_notifications: bool
    ai_notifications: bool
    sprint_events: bool = True
    milestone_events: bool = True
    security_events: bool = True
    digest_notifications: bool = False

class NotificationPreferenceResponse(NotificationPreferenceBase):
    user_id: UUID
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UnreadCountResponse(BaseModel):
    count: int
