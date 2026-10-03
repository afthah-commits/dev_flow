import json
from uuid import UUID
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent

SENSITIVE_KEYS = {
    "password", "token", "access_token", "refresh_token", 
    "client_secret", "api_key", "authorization", "cookie", 
    "jwt", "secret", "encryption_key"
}

def sanitize_metadata(metadata: Any) -> Any:
    if isinstance(metadata, dict):
        sanitized = {}
        for k, v in metadata.items():
            if any(sensitive_key in k.lower() for sensitive_key in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_metadata(v)
        return sanitized
    elif isinstance(metadata, list):
        return [sanitize_metadata(item) for item in metadata]
    elif isinstance(metadata, UUID):
        return str(metadata)
    elif hasattr(metadata, "isoformat"):
        return metadata.isoformat()
    return metadata

def record_event(
    db: Session,
    organization_id: UUID,
    event_type: str,
    entity_type: str,
    actor_user_id: Optional[UUID] = None,
    entity_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    team_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    sanitized_metadata = sanitize_metadata(metadata) if metadata else None
    
    event = AuditEvent(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        project_id=project_id,
        team_id=team_id,
        metadata_=sanitized_metadata,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
