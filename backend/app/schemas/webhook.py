from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class WebhookEndpointBase(BaseModel):
    name: str
    url: str
    active: bool = True
    subscribed_events: List[str]

class WebhookEndpointCreate(WebhookEndpointBase):
    pass

class WebhookEndpointUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    active: Optional[bool] = None
    subscribed_events: Optional[List[str]] = None

class WebhookEndpointResponse(WebhookEndpointBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WebhookDeliveryResponse(BaseModel):
    id: str
    webhook_id: str
    event_type: str
    status: str
    http_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    attempt_count: int
    error_message: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    response_body: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
