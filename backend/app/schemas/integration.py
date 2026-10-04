import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class IntegrationBase(BaseModel):
    provider: str
    name: str
    status: str = "ACTIVE"
    enabled: bool = True
    configuration: Optional[Dict[str, Any]] = None

class IntegrationCreate(IntegrationBase):
    pass

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    enabled: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None

class IntegrationResponse(IntegrationBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    last_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class IntegrationLogResponse(BaseModel):
    id: str
    integration_id: str
    event_type: str
    status: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IntegrationEventResponse(BaseModel):
    id: str
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IntegrationDeliveryResponse(BaseModel):
    id: str
    event_id: str
    integration_id: str
    status: str
    attempts: int
    response_status: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
