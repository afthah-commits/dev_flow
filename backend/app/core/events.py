from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
import uuid
import json

from app.models.integration import IntegrationEvent, IntegrationDelivery, Integration, EmailDelivery
from app.models.audit import AuditEvent

def publish_event(
    db: Session,
    organization_id: str,
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
):
    # Create the event
    event = IntegrationEvent(
        organization_id=organization_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Find active integrations for this org
    integrations = db.query(Integration).filter(
        Integration.organization_id == organization_id,
        Integration.enabled == True,
        Integration.status == "ACTIVE"
    ).all()

    for integration in integrations:
        delivery = IntegrationDelivery(
            event_id=event.id,
            integration_id=integration.id,
            status="PENDING",
            idempotency_key=f"{event.id}-{integration.id}"
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        
        # In a real app we'd dispatch to a background worker like Celery here.
        # But we process immediately for local constraints.
        process_delivery(db, delivery.id)
        
def process_delivery(db: Session, delivery_id: str):
    delivery = db.query(IntegrationDelivery).filter(IntegrationDelivery.id == delivery_id).first()
    if not delivery:
        return
        
    delivery.status = "PROCESSING"
    delivery.attempts += 1
    db.commit()
    
    integration = db.query(Integration).filter(Integration.id == delivery.integration_id).first()
    event = db.query(IntegrationEvent).filter(IntegrationEvent.id == delivery.event_id).first()
    
    try:
        if integration.provider == "SLACK":
            # Mock Slack Delivery
            delivery.status = "DELIVERED"
            delivery.response_status = 200
        elif integration.provider == "GOOGLE_CALENDAR":
            # Mock Calendar Delivery
            delivery.status = "DELIVERED"
            delivery.response_status = 200
        elif integration.provider == "EMAIL":
            # Mock Email Delivery
            email = EmailDelivery(
                organization_id=integration.organization_id,
                to_address="mock@example.com",
                subject=f"Event {event.event_type}",
                body=json.dumps(event.payload)
            )
            db.add(email)
            delivery.status = "DELIVERED"
            delivery.response_status = 200
        else:
            # Generic webhook or mock
            delivery.status = "DELIVERED"
            delivery.response_status = 200
            
    except Exception as e:
        delivery.status = "FAILED"
        delivery.error_message = str(e)
        
        db.add(AuditEvent(
            organization_id=uuid.UUID(integration.organization_id),
            event_type="integration.delivery_failed",
            entity_id=integration.id
        ))

    db.commit()
