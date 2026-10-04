from sqlalchemy import Integer
import uuid
import enum
from sqlalchemy import Column, String, Text, Date, DateTime, func, ForeignKey, Uuid, Enum, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ProjectStatus(str, enum.Enum):
    PLANNING = "Planning"
    ACTIVE = "Active"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"

class ProjectPriority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class Project(Base):
    __tablename__ = "projects"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id"), nullable=True, index=True)
    owner_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False, index=True)
    key = Column(String, nullable=True, index=True)
    task_seq_num = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ProjectStatus, native_enum=False), default=ProjectStatus.PLANNING, nullable=False, index=True)
    priority = Column(Enum(ProjectPriority, native_enum=False), default=ProjectPriority.MEDIUM, nullable=False, index=True)
    tech_stack = Column(JSON, default=list)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="projects")
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    github_repository = relationship("ProjectGitHubRepository", back_populates="project", uselist=False, cascade="all, delete-orphan")
    ai_conversations = relationship("AIConversation", back_populates="project", cascade="all, delete-orphan")
    sprints = relationship("Sprint", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")

