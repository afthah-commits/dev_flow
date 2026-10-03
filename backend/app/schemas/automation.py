from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AutomationBase(BaseModel):
    name: str
    description: Optional[str] = None
    enabled: bool = True
    trigger_type: str
    configuration: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: List[Dict[str, Any]]
    execution_mode: str = "EVENT"

class AutomationCreate(AutomationBase):
    pass

class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    trigger_type: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    execution_mode: Optional[str] = None

class AutomationResponse(AutomationBase):
    id: str
    organization_id: str
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AutomationActionExecutionResponse(BaseModel):
    id: str
    execution_id: str
    action_type: str
    status: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AutomationExecutionResponse(BaseModel):
    id: str
    automation_id: str
    organization_id: str
    trigger_event: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    execution_context: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    
    action_executions: Optional[List[AutomationActionExecutionResponse]] = []

    class Config:
        from_attributes = True
