import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.integration import Integration, IntegrationLog
from app.schemas.integration import IntegrationCreate, IntegrationUpdate, IntegrationResponse, IntegrationLogResponse
from app.models.audit import AuditEvent

router = APIRouter()

@router.get("", response_model=List[IntegrationResponse])
def list_integrations(
    organization_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return db.query(Integration).filter(Integration.organization_id == organization_id).all()

@router.post("", response_model=IntegrationResponse)
def create_integration(
    organization_id: str,
    integration_in: IntegrationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    integration = Integration(
        organization_id=organization_id,
        provider=integration_in.provider,
        name=integration_in.name,
        status=integration_in.status,
        configuration=integration_in.configuration
    )
    db.add(integration)
    
    audit = AuditEvent(organization_id=uuid.UUID(str(organization_id)), event_type="integration.created", entity_type="INTEGRATION", entity_id=None, metadata_={"provider": integration.provider})
    db.add(audit)
    
    db.commit()
    db.refresh(integration)
    return integration

@router.delete("/{integration_id}")
def delete_integration(
    integration_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404)
    db.delete(integration)
    db.commit()
    return {"ok": True}
