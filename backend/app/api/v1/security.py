from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.security import UserSession
from app.models.audit import AuditEvent
from datetime import datetime

router = APIRouter()

class SessionResponse(BaseModel):
    id: UUID
    device_name: Optional[str]
    browser: Optional[str]
    operating_system: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    last_seen_at: datetime
    is_current: bool

    class Config:
        from_attributes = True

@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at == None
    ).order_by(UserSession.last_seen_at.desc()).all()
    
    result = []
    for s in sessions:
        # In a real app we'd compare token hash, but we'll simplify for now
        is_current = False
        result.append(SessionResponse(
            id=s.id,
            device_name=s.device_name,
            browser=s.browser,
            operating_system=s.operating_system,
            ip_address=s.ip_address,
            created_at=s.created_at,
            last_seen_at=s.last_seen_at,
            is_current=is_current
        ))
    return result

@router.delete("/sessions/{session_id}", status_code=204)
def revoke_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.revoked_at = datetime.now()
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="session.revoked"))
    db.commit()

@router.post("/sessions/revoke-all", status_code=204)
def revoke_all_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at == None
    ).all()
    
    for s in sessions:
        s.revoked_at = datetime.now()
        
    db.commit()

from app.models.security import LoginEvent
class LoginEventResponse(BaseModel):
    id: UUID
    timestamp: datetime
    success: bool
    ip_address: Optional[str]
    user_agent: Optional[str]
    failure_reason: Optional[str]
    device_info: Optional[str]

    class Config:
        from_attributes = True

@router.get("/login-history", response_model=List[LoginEventResponse])
def get_login_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20
):
    events = db.query(LoginEvent).filter(LoginEvent.user_id == current_user.id).order_by(LoginEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return events

import json
import secrets

@router.post("/mfa/setup")
def mfa_setup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA already enabled")
        
    secret = "MOCK_MFA_SECRET_" + secrets.token_hex(8)
    current_user.mfa_secret = secret
    db.commit()
    
    return {
        "secret": secret,
        "uri": f"otpauth://totp/DevFlow:{current_user.email}?secret={secret}&issuer=DevFlow"
    }

@router.post("/mfa/verify")
def mfa_verify(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Mock MFA verify (always accept '123456' for testing)
    if code != "123456" and code != "000000":
        raise HTTPException(status_code=400, detail="Invalid MFA code")
        
    current_user.mfa_enabled = True
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="mfa.enabled"))
    recovery_codes = [secrets.token_hex(4) + "-" + secrets.token_hex(4) for _ in range(10)]
    current_user.mfa_recovery_codes = json.dumps(recovery_codes)
    db.commit()
    
    return {"message": "MFA enabled", "recovery_codes": recovery_codes}

@router.post("/mfa/disable")
def mfa_disable(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA not enabled")
        
    if code != "123456" and code != "000000":
        raise HTTPException(status_code=400, detail="Invalid MFA code")
        
    current_user.mfa_enabled = False
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="mfa.disabled"))
    current_user.mfa_secret = None
    current_user.mfa_recovery_codes = None
    db.commit()
    
    return {"message": "MFA disabled"}
