from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
import hashlib
import os
import datetime

from app.api import deps
from app.models.user import User
from app.models.organization import OrganizationInvitation, OrganizationRole, OrganizationMember
from pydantic import BaseModel, EmailStr
from uuid import UUID

router = APIRouter()

class InviteCreate(BaseModel):
    email: EmailStr
    role: OrganizationRole

@router.post("")
def create_invitation(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    current_user: User = Depends(deps.get_current_user),
    invite_in: InviteCreate
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id missing")
    
    # Require admin or owner to invite
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role.in_([OrganizationRole.OWNER, OrganizationRole.ADMIN])
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    raw_token = os.urandom(32).hex()
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    
    inv = OrganizationInvitation(
        organization_id=org_id,
        email=invite_in.email,
        role=invite_in.role,
        invited_by=current_user.id,
        token_hash=hashed_token,
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    
    return {
        "message": "Invitation created",
        "development_invite_link": f"http://localhost:5173/invite?token={raw_token}&id={inv.id}"
    }
