from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from app.api.deps import get_db, get_current_user, get_current_organization_id, require_organization_member
from app.models.user import User
from app.models.organization import OrganizationRole
from app.models.workflow import CustomField, CustomFieldValue
from app.schemas.custom_field import CustomFieldResponse, CustomFieldCreate, CustomFieldUpdate

router = APIRouter()

@router.get("", response_model=List[CustomFieldResponse])
def get_custom_fields(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    require_organization_member(db, current_user.id, org_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER])
    return db.query(CustomField).filter(CustomField.organization_id == org_id).all()

@router.post("", response_model=CustomFieldResponse)
def create_custom_field(
    field_in: CustomFieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    require_organization_member(db, current_user.id, org_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    field = CustomField(
        organization_id=org_id,
        name=field_in.name,
        key=field_in.key,
        field_type=field_in.field_type,
        description=field_in.description,
        is_required=field_in.is_required,
        is_active=field_in.is_active,
        configuration=field_in.configuration
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field
