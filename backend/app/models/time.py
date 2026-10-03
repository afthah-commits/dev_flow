import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Uuid, Enum, Boolean, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class TimeEntrySource(str, enum.Enum):
    TIMER = "TIMER"
    MANUAL = "MANUAL"

class TimeEntry(Base):
    __tablename__ = "time_entries"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    sprint_id = Column(Uuid, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True, index=True)
    
    description = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    billable = Column(Boolean, default=False, nullable=False, index=True)
    source = Column(Enum(TimeEntrySource, native_enum=False), default=TimeEntrySource.MANUAL, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    project = relationship("Project")
    task = relationship("Task")

class ActiveTimer(Base):
    __tablename__ = "active_timers"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='uq_active_timer_user_org'),
    )

    user = relationship("User")
    project = relationship("Project")
    task = relationship("Task")
