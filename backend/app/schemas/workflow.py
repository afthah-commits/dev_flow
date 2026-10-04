from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.workflow import (
    WorkflowEntityType,
    WorkflowConditionType,
    WorkflowActionType,
    WorkflowApprovalStatus
)

class WorkflowStateBase(BaseModel):
    name: str
    key: str
    description: Optional[str] = None
    position: int = 0
    color: Optional[str] = None
    is_initial: bool = False
    is_terminal: bool = False

class WorkflowStateCreate(WorkflowStateBase):
    pass

class WorkflowStateResponse(WorkflowStateBase):
    id: UUID
    workflow_id: UUID

    class Config:
        from_attributes = True

class WorkflowTransitionBase(BaseModel):
    name: str
    from_state_id: UUID
    to_state_id: UUID
    position: int = 0
    requires_approval: bool = False

class WorkflowTransitionCreate(WorkflowTransitionBase):
    pass

class WorkflowTransitionResponse(WorkflowTransitionBase):
    id: UUID
    workflow_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    entity_type: WorkflowEntityType
    is_active: bool = True

class WorkflowCreate(WorkflowBase):
    states: Optional[List[WorkflowStateCreate]] = []
    transitions: Optional[List[WorkflowTransitionCreate]] = []

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class WorkflowResponse(WorkflowBase):
    id: UUID
    organization_id: UUID
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    states: List[WorkflowStateResponse] = []
    transitions: List[WorkflowTransitionResponse] = []

    class Config:
        from_attributes = True
