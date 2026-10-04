from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class APIKeyBase(BaseModel):
    name: str
    scopes: List[str]

class APIKeyCreate(APIKeyBase):
    expires_in_days: Optional[int] = None

class APIKeyResponse(APIKeyBase):
    id: str
    organization_id: str
    key_prefix: str
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
