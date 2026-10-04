import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class EntityType(str, enum.Enum):
    PROJECT = "PROJECT"
    TASK = "TASK"
    SPRINT = "SPRINT"
    RELEASE = "RELEASE"
    DEPLOYMENT = "DEPLOYMENT"
    PIPELINE = "PIPELINE"
    MILESTONE = "MILESTONE"
    DISCUSSION = "DISCUSSION"

class DiscussionStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"

class Comment(Base):
    __tablename__ = "comments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(SQLEnum(EntityType, name="comment_entity_type"), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True, index=True)
    
    content = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    is_pinned = Column(Boolean, default=False)
    client_visible = Column(Boolean, default=False, nullable=False, server_default="0")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    replies = relationship("Comment", backref="parent_comment", remote_side=[id])
    reactions = relationship("CommentReaction", back_populates="comment", cascade="all, delete-orphan")


class CommentReaction(Base):
    __tablename__ = "comment_reactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reaction = Column(String(50), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', 'reaction', name='uq_comment_user_reaction'),
    )

    comment = relationship("Comment", back_populates="reactions")


class Discussion(Base):
    __tablename__ = "discussions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(SQLEnum(DiscussionStatus, name="discussion_status"), default=DiscussionStatus.OPEN, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    entity_type = Column(SQLEnum(EntityType, name="attachment_entity_type"), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_key = Column(String(255), nullable=False, unique=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
