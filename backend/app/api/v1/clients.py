from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db, get_current_user, get_current_organization_id
from app.models.user import User
from app.models.organization import Organization
from app.schemas.client import ClientResponse, ClientCreate, ClientUpdate
from app.services import client_service
from app.api.deps import require_organization_member, get_db, get_current_user, get_current_organization_id
from app.models.organization import OrganizationRole

router = APIRouter()

@router.get("", response_model=List[ClientResponse])
def get_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    require_organization_member(db, current_user.id, org_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER])
    return client_service.get_clients(db, org_id)

@router.post("", response_model=ClientResponse)
def create_client(
    client_in: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    require_organization_member(db, current_user.id, org_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    return client_service.create_client(db, org_id, current_user.id, client_in)

@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    require_organization_member(db, current_user.id, org_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER])
    return client_service.get_client(db, client_id, org_id)
