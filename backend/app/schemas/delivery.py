from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.delivery import ReleaseStatus, ReleaseType, DeploymentStatus, DeploymentProvider, PipelineStatus, EnvironmentType, EnvironmentStatus

class ReleaseBase(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    release_type: ReleaseType = ReleaseType.MINOR
    target_environment: Optional[str] = None
    git_tag: Optional[str] = None
    target_commit_sha: Optional[str] = None
    planned_at: Optional[datetime] = None

class ReleaseCreate(ReleaseBase):
    pass

class ReleaseUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    release_type: Optional[ReleaseType] = None
    target_environment: Optional[str] = None
    git_tag: Optional[str] = None
    target_commit_sha: Optional[str] = None
    planned_at: Optional[datetime] = None

class ReleaseResponse(ReleaseBase):
    id: UUID
    organization_id: UUID
    project_id: UUID
    status: ReleaseStatus
    released_at: Optional[datetime] = None
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReadinessCheck(BaseModel):
    name: str
    status: str
    message: str

class ReleaseReadiness(BaseModel):
    ready: bool
    score: int
    checks: List[ReadinessCheck]
    
class ReleaseApprovalCreate(BaseModel):
    reviewer_id: UUID
    comment: Optional[str] = None
    
class ReleaseApprovalResponse(BaseModel):
    id: UUID
    release_id: UUID
    requested_by_id: UUID
    reviewer_id: UUID
    status: str
    comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EnvironmentBase(BaseModel):
    name: str
    slug: Optional[str] = None
    environment_type: EnvironmentType = EnvironmentType.DEVELOPMENT
    status: EnvironmentStatus = EnvironmentStatus.ACTIVE
    description: Optional[str] = None
    url: Optional[str] = None
    branch: Optional[str] = None
    is_default: bool = False
    is_active: bool = True

class EnvironmentCreate(EnvironmentBase):
    pass

class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    environment_type: Optional[EnvironmentType] = None
    status: Optional[EnvironmentStatus] = None
    description: Optional[str] = None
    url: Optional[str] = None
    branch: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class EnvironmentResponse(EnvironmentBase):
    id: UUID
    organization_id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DeploymentBase(BaseModel):
    environment_id: Optional[UUID] = None
    provider: DeploymentProvider = DeploymentProvider.MOCK
    deployment_key: Optional[str] = None
    version: Optional[str] = None
    branch: Optional[str] = None

class DeploymentCreate(DeploymentBase):
    pass

class DeploymentResponse(DeploymentBase):
    id: UUID
    organization_id: UUID
    project_id: UUID
    release_id: Optional[UUID] = None
    deployment_key: Optional[str] = None
    version: Optional[str] = None
    branch: Optional[str] = None
    status: DeploymentStatus
    deployment_url: Optional[str] = None
    commit_sha: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    triggered_by_id: Optional[UUID] = None
    error_message: Optional[str] = None
    previous_deployment_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PipelineRunBase(BaseModel):
    provider: DeploymentProvider = DeploymentProvider.MOCK
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    workflow_name: Optional[str] = None

class PipelineRunCreate(PipelineRunBase):
    pass

class PipelineRunResponse(PipelineRunBase):
    id: UUID
    organization_id: UUID
    project_id: UUID
    release_id: Optional[UUID] = None
    deployment_id: Optional[UUID] = None
    status: PipelineStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    workflow_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DeliveryMetrics(BaseModel):
    deployment_frequency: float
    successful_deployment_rate: float
    failed_deployment_rate: float
    avg_deployment_duration_seconds: float
    release_frequency: float
    avg_release_cycle_time_days: float
    pipeline_success_rate: float
    rollback_frequency: float
    avg_lead_time_days: float

class DoraMetrics(BaseModel):
    deployment_frequency: str
    lead_time_for_changes: str
    change_failure_rate: str
    mean_time_to_recovery: str
