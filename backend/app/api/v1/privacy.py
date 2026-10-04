from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any
import uuid
from datetime import datetime, timezone

from app.api import deps
from app.models.user import User
from app.models.audit import AuditEvent
from app.models.governance import UserDeletionRequest

router = APIRouter()

@router.get("/me")
def get_my_privacy_data(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "data_collected": ["Email", "Full Name", "IP Addresses (for security)", "Activity Logs"]
    }

@router.post("/export")
def request_my_data_export(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="privacy.export_requested"))
    db.commit()
    return {"message": "Data export requested. You will receive an email when it is ready."}

@router.post("/delete-request")
def request_account_deletion(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    existing = db.query(UserDeletionRequest).filter(
        UserDeletionRequest.user_id == str(current_user.id),
        UserDeletionRequest.status == "REQUESTED"
    ).first()
    if existing:
        return {"message": "Deletion already requested"}
        
    req = UserDeletionRequest(user_id=str(current_user.id))
    db.add(req)
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="privacy.deletion_requested"))
    db.commit()
    return {"message": "Account deletion requested safely."}

