from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class NotificationBase(BaseModel):
    project_id: Optional[UUID] = None
    type: str
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
    deadline_notifications: bool
    project_health_notifications: bool
    github_notifications: bool
    ai_notifications: bool

class NotificationPreferenceResponse(NotificationPreferenceBase):
    user_id: UUID
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UnreadCountResponse(BaseModel):
    count: int
