import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyResponse
from app.models.audit import AuditEvent
import secrets
import hashlib
from datetime import datetime, timezone, timedelta

router = APIRouter()

@router.get("", response_model=List[APIKeyResponse])
def list_api_keys(
    organization_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return db.query(APIKey).filter(APIKey.organization_id == organization_id).all()

@router.post("")
def create_api_key(
    organization_id: str,
    key_in: APIKeyCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    raw_key = secrets.token_urlsafe(32)
    key_prefix = raw_key[:8]
    key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    
    expires_at = None
    if key_in.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=key_in.expires_in_days)
        
    api_key = APIKey(
        organization_id=organization_id,
        name=key_in.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=key_in.scopes,
        expires_at=expires_at
    )
    db.add(api_key)
    audit = AuditEvent(organization_id=uuid.UUID(str(organization_id)), event_type="api_key.created", entity_type="API_KEY", entity_id=None, metadata_={"name": api_key.name})
    db.add(audit)
    db.commit()
    db.refresh(api_key)
    
    # Expose raw key ONCE
    return {
        "id": api_key.id,
        "organization_id": api_key.organization_id,
        "key_prefix": api_key.key_prefix,
        "raw_key": raw_key,
        "scopes": api_key.scopes,
        "created_at": api_key.created_at
    }

@router.post("/{key_id}/revoke")
def revoke_api_key(
    key_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404)
    api_key.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}
