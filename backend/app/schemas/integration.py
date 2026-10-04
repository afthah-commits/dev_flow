from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class IntegrationBase(BaseModel):
    provider: str
    name: str
    status: str = "ACTIVE"
    configuration: Optional[Dict[str, Any]] = None

class IntegrationCreate(IntegrationBase):
    pass

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None

class IntegrationResponse(IntegrationBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IntegrationLogResponse(BaseModel):
    id: str
    integration_id: str
    event_type: str
    status: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
