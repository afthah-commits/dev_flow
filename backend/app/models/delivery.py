import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Uuid, Enum, Boolean, Integer, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ReleaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    READY = "READY"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"

class ReleaseType(str, enum.Enum):
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    PATCH = "PATCH"
    HOTFIX = "HOTFIX"

class Release(Base):
    __tablename__ = "releases"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String, nullable=False)
    version = Column(String, nullable=False) # e.g. v1.0.0
    description = Column(Text, nullable=True)
    status = Column(Enum(ReleaseStatus, native_enum=False), default=ReleaseStatus.DRAFT, nullable=False, index=True)
    release_type = Column(Enum(ReleaseType, native_enum=False), default=ReleaseType.MINOR, nullable=False)
    
    target_environment = Column(String, nullable=True)
    git_tag = Column(String, nullable=True)
    target_commit_sha = Column(String, nullable=True)
    
    planned_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    
    created_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('project_id', 'version', name='uq_release_version_project'),
    )
    
    project = relationship("Project")
    created_by = relationship("User")
    tasks = relationship("ReleaseTask", back_populates="release", cascade="all, delete-orphan")
    pull_requests = relationship("ReleasePullRequest", back_populates="release", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="release", cascade="all, delete-orphan")
    pipeline_runs = relationship("PipelineRun", back_populates="release", cascade="all, delete-orphan")

class ReleaseTask(Base):
    __tablename__ = "release_tasks"
    release_id = Column(Uuid, ForeignKey("releases.id", ondelete="CASCADE"), primary_key=True)
    task_id = Column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    release = relationship("Release", back_populates="tasks")
    task = relationship("Task")

class ReleasePullRequest(Base):
    __tablename__ = "release_pull_requests"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    release_id = Column(Uuid, ForeignKey("releases.id", ondelete="CASCADE"), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False)
    pr_title = Column(String, nullable=True)
    pr_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('release_id', 'pr_number', name='uq_release_pr'),
    )
    
    release = relationship("Release", back_populates="pull_requests")


class EnvironmentType(str, enum.Enum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    PREVIEW = "PREVIEW"

class EnvironmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"

class Environment(Base):
    __tablename__ = "environments"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String, nullable=False)
    slug = Column(String, nullable=True)
    environment_type = Column(Enum(EnvironmentType, native_enum=False), default=EnvironmentType.DEVELOPMENT, nullable=False)
    status = Column(Enum(EnvironmentStatus, native_enum=False), default=EnvironmentStatus.ACTIVE, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('project_id', 'name', name='uq_environment_name_project'),
    )

class DeploymentStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    BUILDING = "BUILDING"
    DEPLOYING = "DEPLOYING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ROLLED_BACK = "ROLLED_BACK"


class DeploymentProvider(str, enum.Enum):
    MOCK = "MOCK"
    GITHUB_ACTIONS = "GITHUB_ACTIONS"
    MANUAL = "MANUAL"

class Deployment(Base):
    __tablename__ = "deployments"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    release_id = Column(Uuid, ForeignKey("releases.id", ondelete="SET NULL"), nullable=True, index=True)
    environment_id = Column(Uuid, ForeignKey("environments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    deployment_key = Column(String, nullable=True)
    version = Column(String, nullable=True)
    branch = Column(String, nullable=True)

    
    status = Column(Enum(DeploymentStatus, native_enum=False), default=DeploymentStatus.QUEUED, nullable=False, index=True)
    deployment_url = Column(String, nullable=True)
    commit_sha = Column(String, nullable=True, index=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_seconds = Column(Integer, nullable=True)
    
    triggered_by_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    provider = Column(Enum(DeploymentProvider, native_enum=False), default=DeploymentProvider.MOCK, nullable=False)
    error_message = Column(Text, nullable=True)
    
    previous_deployment_id = Column(Uuid, ForeignKey("deployments.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    release = relationship("Release", back_populates="deployments")
    environment = relationship("Environment")
    triggered_by = relationship("User")
    previous_deployment = relationship("Deployment", remote_side=[id])

class PipelineStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    release_id = Column(Uuid, ForeignKey("releases.id", ondelete="SET NULL"), nullable=True, index=True)
    deployment_id = Column(Uuid, ForeignKey("deployments.id", ondelete="SET NULL"), nullable=True, index=True)
    
    provider = Column(Enum(DeploymentProvider, native_enum=False), default=DeploymentProvider.MOCK, nullable=False)
    branch = Column(String, nullable=True)
    commit_sha = Column(String, nullable=True, index=True)
    
    status = Column(Enum(PipelineStatus, native_enum=False), default=PipelineStatus.QUEUED, nullable=False, index=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    workflow_name = Column(String, nullable=True)
    workflow_url = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    release = relationship("Release", back_populates="pipeline_runs")
    deployment = relationship("Deployment")
