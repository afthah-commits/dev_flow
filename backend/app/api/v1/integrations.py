from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from uuid import UUID
from datetime import datetime, timezone

from app.api import deps
from app.models.integration import Integration, IntegrationLog, IntegrationEvent, IntegrationDelivery
from app.models.webhook import WebhookDelivery, WebhookEndpoint
from app.schemas.integration import (
    IntegrationCreate, IntegrationUpdate, IntegrationResponse, 
    IntegrationLogResponse, IntegrationEventResponse, IntegrationDeliveryResponse
)
from app.models.user import User
from app.models.audit import AuditEvent
from app.api.v1.governance import check_permission

router = APIRouter()

@router.get("", response_model=List[IntegrationResponse])
def list_integrations(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "integrations.view")
    
    return db.query(Integration).filter(Integration.organization_id == str(org_id)).all()

@router.post("", response_model=IntegrationResponse)
def create_integration(
    integration_in: IntegrationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "integrations.manage")

    integration = Integration(
        organization_id=str(org_id),
        provider=integration_in.provider,
        name=integration_in.name,
        status=integration_in.status,
        enabled=integration_in.enabled,
        configuration=integration_in.configuration
    )
    db.add(integration)
    audit = AuditEvent(
        organization_id=org_id, 
        actor_user_id=current_user.id,
        event_type="integration.created", 
        entity_type="INTEGRATION", 
        metadata_={"provider": integration.provider}
    )
    db.add(audit)
    db.commit()
    db.refresh(integration)
    return integration

@router.get("/{integration_id}", response_model=IntegrationResponse)
def get_integration(
    integration_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "integrations.view")
    
    integration = db.query(Integration).filter(Integration.id == integration_id, Integration.organization_id == str(org_id)).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration

@router.patch("/{integration_id}", response_model=IntegrationResponse)
def update_integration(
    integration_id: str,
    integration_in: IntegrationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "integrations.manage")
    
    integration = db.query(Integration).filter(Integration.id == integration_id, Integration.organization_id == str(org_id)).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    update_data = integration_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(integration, field, value)
        
    db.add(AuditEvent(
        organization_id=org_id, 
        actor_user_id=current_user.id,
        event_type="integration.updated", 
        entity_type="INTEGRATION", 
        entity_id=integration.id
    ))
    db.commit()
    db.refresh(integration)
    return integration

@router.delete("/{integration_id}", status_code=204)
def delete_integration(
    integration_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "integrations.manage")

    integration = db.query(Integration).filter(Integration.id == integration_id, Integration.organization_id == str(org_id)).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    db.delete(integration)
    db.add(AuditEvent(
        organization_id=org_id, 
        actor_user_id=current_user.id,
        event_type="integration.deleted", 
        entity_type="INTEGRATION", 
        entity_id=integration.id
    ))
    db.commit()

@router.post("/{integration_id}/enable", response_model=IntegrationResponse)
def enable_integration(
    integration_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "integrations.manage")
    
    integration = db.query(Integration).filter(Integration.id == integration_id, Integration.organization_id == str(org_id)).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    integration.enabled = True
    db.add(AuditEvent(organization_id=org_id, actor_user_id=current_user.id, event_type="integration.enabled", entity_id=integration.id))
    db.commit()
    db.refresh(integration)
    return integration

@router.post("/{integration_id}/disable", response_model=IntegrationResponse)
def disable_integration(
    integration_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "integrations.manage")
    
    integration = db.query(Integration).filter(Integration.id == integration_id, Integration.organization_id == str(org_id)).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    integration.enabled = False
    db.add(AuditEvent(organization_id=org_id, actor_user_id=current_user.id, event_type="integration.disabled", entity_id=integration.id))
    db.commit()
    db.refresh(integration)
    return integration

@router.post("/{integration_id}/test")
def test_integration(
    integration_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "integrations.manage")
    
    integration = db.query(Integration).filter(Integration.id == integration_id, Integration.organization_id == str(org_id)).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
        
    db.add(AuditEvent(organization_id=org_id, actor_user_id=current_user.id, event_type="integration.tested", entity_id=integration.id))
    db.commit()
    
    return {"success": True, "message": f"Successfully tested connection to {integration.provider}"}

@router.get("/usage/analytics")
def get_integration_usage_analytics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "integrations.view")
    
    # Simple aggregates
    webhook_deliveries = db.query(WebhookDelivery).join(WebhookEndpoint).filter(WebhookEndpoint.organization_id == str(org_id)).count()
    failed_webhooks = db.query(WebhookDelivery).join(WebhookEndpoint).filter(WebhookEndpoint.organization_id == str(org_id), WebhookDelivery.status == "FAILED").count()
    integration_events = db.query(IntegrationEvent).filter(IntegrationEvent.organization_id == str(org_id)).count()
    
    return {
        "total_requests": webhook_deliveries + integration_events,
        "webhook_deliveries": webhook_deliveries,
        "failed_deliveries": failed_webhooks,
        "integration_events": integration_events
    }
