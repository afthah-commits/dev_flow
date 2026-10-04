from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.infrastructure import DeploymentApprovalStatus, ServiceHealthStatus, DeploymentIncidentStatus

class DeploymentApprovalBase(BaseModel):
    deployment_id: UUID
    status: DeploymentApprovalStatus = DeploymentApprovalStatus.PENDING
    comment: Optional[str] = None

class DeploymentApprovalCreate(DeploymentApprovalBase):
    pass

class DeploymentApprovalResponse(DeploymentApprovalBase):
    id: UUID
    organization_id: UUID
    requested_by_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EnvironmentVariableBase(BaseModel):
    key: str
    is_secret: bool = False

class EnvironmentVariableCreate(EnvironmentVariableBase):
    value: str

class EnvironmentVariableUpdate(BaseModel):
    value: Optional[str] = None
    is_secret: Optional[bool] = None

class EnvironmentVariableResponse(EnvironmentVariableBase):
    id: UUID
    organization_id: UUID
    environment_id: UUID
    value: str = Field(..., description="The value of the variable. If is_secret is True, this will be masked.")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ServiceHealthBase(BaseModel):
    service_name: str
    status: ServiceHealthStatus = ServiceHealthStatus.UNKNOWN
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None

class ServiceHealthCreate(ServiceHealthBase):
    pass

class ServiceHealthResponse(ServiceHealthBase):
    id: UUID
    organization_id: UUID
    environment_id: UUID
    last_checked_at: datetime

    class Config:
        from_attributes = True

class DeploymentIncidentBase(BaseModel):
    deployment_id: Optional[UUID] = None
    environment_id: UUID
    severity: str
    title: str
    description: Optional[str] = None
    status: DeploymentIncidentStatus = DeploymentIncidentStatus.OPEN

class DeploymentIncidentCreate(DeploymentIncidentBase):
    pass

class DeploymentIncidentUpdate(BaseModel):
    severity: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[DeploymentIncidentStatus] = None

class DeploymentIncidentResponse(DeploymentIncidentBase):
    id: UUID
    organization_id: UUID
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
