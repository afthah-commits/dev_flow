import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Uuid, Enum, Float, Integer
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SprintStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Sprint(Base):
    __tablename__ = "sprints"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    key = Column(String, nullable=False, index=True, unique=True)
    goal = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(SprintStatus, native_enum=False), default=SprintStatus.PLANNED, nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True, index=True)
    capacity = Column(Float, nullable=True)
    created_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="sprints")
    created_by = relationship("User", foreign_keys=[created_by_id])
    tasks = relationship("Task", back_populates="sprint")
    snapshots = relationship("SprintSnapshot", back_populates="sprint", cascade="all, delete-orphan")

class SprintSnapshot(Base):
    __tablename__ = "sprint_snapshots"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    sprint_id = Column(Uuid, ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_points = Column(Float, nullable=False, default=0.0)
    completed_points = Column(Float, nullable=False, default=0.0)
    remaining_points = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sprint = relationship("Sprint", back_populates="snapshots")
