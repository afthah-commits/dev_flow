import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.webhook import WebhookEndpoint, WebhookDelivery
from app.schemas.webhook import WebhookEndpointCreate, WebhookEndpointUpdate, WebhookEndpointResponse, WebhookDeliveryResponse
from app.models.audit import AuditEvent
import secrets

router = APIRouter()

def _require_org_access(db: Session, current_user: User, organization_id: str) -> str:
    """Phase 31: validate membership before touching org-scoped webhooks."""
    try:
        org_uuid = uuid.UUID(str(organization_id))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=404, detail="Webhook not found")
    deps.require_organization_member(db, current_user.id, org_uuid)
    return str(org_uuid)

@router.get("", response_model=List[WebhookEndpointResponse])
def list_webhooks(
    organization_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    org_id = _require_org_access(db, current_user, organization_id)
    return db.query(WebhookEndpoint).filter(WebhookEndpoint.organization_id == org_id).all()

@router.post("", response_model=WebhookEndpointResponse)
def create_webhook(
    organization_id: str,
    webhook_in: WebhookEndpointCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    org_id = _require_org_access(db, current_user, organization_id)
    secret = secrets.token_urlsafe(32) # In reality, return once. Here stored directly for mock.
    webhook = WebhookEndpoint(
        organization_id=org_id,
        name=webhook_in.name,
        url=webhook_in.url,
        active=webhook_in.active,
        subscribed_events=webhook_in.subscribed_events,
        encrypted_secret=secret
    )
    db.add(webhook)
    audit = AuditEvent(organization_id=uuid.UUID(str(organization_id)), event_type="webhook.created", entity_type="WEBHOOK", entity_id=None, metadata_={"url": webhook.url})
    db.add(audit)
    db.commit()
    db.refresh(webhook)
    return webhook

@router.delete("/{webhook_id}")
def delete_webhook(
    webhook_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    webhook = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404)
    _require_org_access(db, current_user, webhook.organization_id)
    db.delete(webhook)
    db.commit()
    return {"ok": True}
