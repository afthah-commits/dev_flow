import uuid
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Uuid, Enum, JSON, Integer, Boolean, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.task import TaskPriority


class ProjectTemplate(Base):
    """Organization-scoped reusable project blueprint (Phase 44).

    Templates hold only relative description of tasks; they never reference
    concrete project/task IDs so they stay fully independent from projects
    created from them.
    """
    __tablename__ = "project_templates"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_archived = Column(Boolean, nullable=False, default=False, server_default="0")
    created_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tasks = relationship(
        "ProjectTemplateTask",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="ProjectTemplateTask.position",
    )


class ProjectTemplateTask(Base):
    """A task definition inside a project template."""
    __tablename__ = "project_template_tasks"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    template_id = Column(Uuid, ForeignKey("project_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, nullable=False, default=0)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Enum(TaskPriority, native_enum=False), nullable=False, default=TaskPriority.MEDIUM)
    # Comma/JSON stored label names and checklist texts; resolved/copied at
    # apply time without referencing concrete project records.
    label_names = Column(JSON, default=list)
    checklist_items = Column(JSON, default=list)

    template = relationship("ProjectTemplate", back_populates="tasks")
