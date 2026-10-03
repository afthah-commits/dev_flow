from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.models.collaboration import EntityType, DiscussionStatus

class CommentBase(BaseModel):
    content: str
    entity_type: Optional[EntityType] = None
    entity_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(CommentBase):
    id: UUID
    organization_id: UUID
    author_id: UUID
    is_edited: bool
    edited_at: Optional[datetime] = None
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ReactionBase(BaseModel):
    reaction: str

class ReactionCreate(ReactionBase):
    pass

class ReactionResponse(ReactionBase):
    id: UUID
    comment_id: UUID
    user_id: UUID

    class Config:
        orm_mode = True

class DiscussionBase(BaseModel):
    title: str
    content: str

class DiscussionCreate(DiscussionBase):
    pass

class DiscussionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[DiscussionStatus] = None

class DiscussionResponse(DiscussionBase):
    id: UUID
    organization_id: UUID
    project_id: UUID
    author_id: UUID
    status: DiscussionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AttachmentBase(BaseModel):
    file_name: str
    file_size: int
    mime_type: str
    entity_type: EntityType
    entity_id: UUID

class AttachmentCreate(AttachmentBase):
    pass

class AttachmentResponse(AttachmentBase):
    id: UUID
    organization_id: UUID
    uploaded_by: UUID
    storage_key: str
    created_at: datetime

    class Config:
        orm_mode = True
