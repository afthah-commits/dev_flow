import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, Date, func, ForeignKey, Uuid, Enum, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MilestoneStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(MilestoneStatus, native_enum=False), default=MilestoneStatus.PLANNED, nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    position = Column(Float, nullable=False, default=0.0)
    created_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="milestones")
    created_by = relationship("User", foreign_keys=[created_by_id])
    tasks = relationship("Task", back_populates="milestone")
