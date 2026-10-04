import uuid
import enum
from sqlalchemy import Column, String, Text, Date, DateTime, func, ForeignKey, Uuid, Enum, JSON, Boolean, Float, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"

class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Label(Base):
    __tablename__ = "labels"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    color = Column(String, nullable=False, default="#808080")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    __table_args__ = (UniqueConstraint('organization_id', 'name', name='uq_label_org_name'),)

class TaskLabel(Base):
    __tablename__ = "task_labels"
    task_id = Column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    label_id = Column(Uuid, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True)

class TaskDependencyType(str, enum.Enum):
    BLOCKS = "BLOCKS"
    RELATES_TO = "RELATES_TO"

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    source_id = Column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type = Column(Enum(TaskDependencyType, native_enum=False), default=TaskDependencyType.BLOCKS, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('source_id', 'target_id', 'dependency_type', name='uq_task_dependency'),)
    
class TaskWatcher(Base):
    __tablename__ = "task_watchers"
    task_id = Column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    task_id = Column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(String, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    position = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    task = relationship("Task", back_populates="checklists")

class TaskTemplate(Base):
    __tablename__ = "task_templates"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    title_template = Column(String, nullable=True)
    description_template = Column(Text, nullable=True)
    priority_template = Column(Enum(TaskPriority, native_enum=False), nullable=True)
    labels_template = Column(JSON, default=list)
    checklist_template = Column(JSON, default=list)
    created_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    sprint_id = Column(Uuid, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True, index=True)
    milestone_id = Column(Uuid, ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True, index=True)
    task_key = Column(String, nullable=True, index=True, unique=True)
    parent_id = Column(Uuid, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    client_visible = Column(Boolean, default=False, nullable=False, server_default="0")
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus, native_enum=False), default=TaskStatus.TODO, nullable=False, index=True)
    priority = Column(Enum(TaskPriority, native_enum=False), default=TaskPriority.MEDIUM, nullable=False, index=True)
    assignee_id = Column(Uuid, ForeignKey("users.id"), nullable=True, index=True)
    creator_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    updated_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    estimate_points = Column(Float, nullable=True)
    estimate_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    position = Column(Float, nullable=False, default=0.0, index=True)
    is_blocked = Column(Boolean, default=False, nullable=False)
    recurring_config = Column(JSON, nullable=True)
    
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    labels = Column(JSON, default=list) # legacy labels
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="tasks")
    sprint = relationship("Sprint", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    
    parent = relationship("Task", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent", cascade="all, delete-orphan")
    
    labels_rel = relationship("Label", secondary="task_labels")
    watchers = relationship("User", secondary="task_watchers")
    checklists = relationship("ChecklistItem", back_populates="task", cascade="all, delete-orphan", order_by="ChecklistItem.position")
    
    blocks = relationship("TaskDependency", foreign_keys=[TaskDependency.source_id], cascade="all, delete-orphan")
    blocked_by = relationship("TaskDependency", foreign_keys=[TaskDependency.target_id], cascade="all, delete-orphan")
