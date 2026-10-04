from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.workflow import CustomFieldType

class CustomFieldBase(BaseModel):
    name: str
    key: str
    field_type: CustomFieldType
    description: Optional[str] = None
    is_required: bool = False
    is_active: bool = True
    configuration: Optional[Dict[str, Any]] = None

class CustomFieldCreate(CustomFieldBase):
    pass

class CustomFieldUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None

class CustomFieldResponse(CustomFieldBase):
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CustomFieldValueBase(BaseModel):
    entity_type: str
    entity_id: UUID
    value: Any

class CustomFieldValueCreate(CustomFieldValueBase):
    pass

class CustomFieldValueResponse(CustomFieldValueBase):
    id: UUID
    custom_field_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
