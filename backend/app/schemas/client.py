from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr

from app.models.client import ClientStatus, ClientUserRole, ClientProjectAccessLevel, ClientRequestStatus, ClientRequestPriority

class ClientBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[ClientStatus] = None

class ClientResponse(ClientBase):
    id: UUID
    organization_id: UUID
    status: ClientStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ClientUserResponse(BaseModel):
    id: UUID
    client_id: UUID
    user_id: UUID
    role: ClientUserRole
    created_at: datetime

    class Config:
        from_attributes = True

class ClientProjectAccessResponse(BaseModel):
    id: UUID
    client_id: UUID
    project_id: UUID
    access_level: ClientProjectAccessLevel
    created_at: datetime

    class Config:
        from_attributes = True

class ClientRequestBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: ClientRequestPriority = ClientRequestPriority.NORMAL
    project_id: Optional[UUID] = None

class ClientRequestCreate(ClientRequestBase):
    pass

class ClientRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ClientRequestStatus] = None
    priority: Optional[ClientRequestPriority] = None

class ClientRequestResponse(ClientRequestBase):
    id: UUID
    organization_id: UUID
    client_id: UUID
    status: ClientRequestStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClientCommentBase(BaseModel):
    body: str

class ClientCommentCreate(ClientCommentBase):
    entity_type: str
    entity_id: UUID

class ClientCommentResponse(ClientCommentBase):
    id: UUID
    client_id: UUID
    entity_type: str
    entity_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
