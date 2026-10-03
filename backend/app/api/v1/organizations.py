from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID
import re

from app.api import deps
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationMemberResponse, OrganizationMemberUpdate
)

router = APIRouter()

def generate_slug(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug if slug else "org"

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    *,
    db: Session = Depends(deps.get_db),
    org_in: OrganizationCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    base_slug = generate_slug(org_in.name)
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(
        **org_in.model_dump(),
        slug=slug,
        created_by=current_user.id
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Add creator as OWNER
    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=OrganizationRole.OWNER
    )
    db.add(member)
    db.commit()

    return org

@router.get("", response_model=List[OrganizationResponse])
def list_organizations(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    orgs = db.query(Organization).join(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id
    ).all()
    return orgs

@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id)
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    return org

@router.patch("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: UUID,
    org_in: OrganizationUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    update_data = org_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)
        
    db.commit()
    db.refresh(org)
    return org

@router.delete("/{organization_id}")
def delete_organization(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id, [OrganizationRole.OWNER])
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    db.delete(org)
    db.commit()
    return {"message": "Organization deleted"}

@router.get("/{organization_id}/members", response_model=List[OrganizationMemberResponse])
def list_members(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id)
    members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == organization_id).all()
    return members

@router.patch("/{organization_id}/members/{member_id}", response_model=OrganizationMemberResponse)
def update_member_role(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: UUID,
    member_id: UUID,
    member_in: OrganizationMemberUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    caller = deps.require_organization_member(db, current_user.id, organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    target_member = db.query(OrganizationMember).filter(
        OrganizationMember.id == member_id,
        OrganizationMember.organization_id == organization_id
    ).first()
    
    if not target_member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    if target_member.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
        
    if target_member.role == OrganizationRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot change role of an owner")
        
    if caller.role == OrganizationRole.ADMIN and member_in.role == OrganizationRole.OWNER:
        raise HTTPException(status_code=400, detail="Admins cannot promote to OWNER")
        
    target_member.role = member_in.role
    db.commit()
    db.refresh(target_member)
    return target_member

@router.delete("/{organization_id}/members/{member_id}")
def remove_member(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: UUID,
    member_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    target_member = db.query(OrganizationMember).filter(
        OrganizationMember.id == member_id,
        OrganizationMember.organization_id == organization_id
    ).first()
    
    if not target_member:
        raise HTTPException(status_code=404, detail="Member not found")

    if target_member.user_id == current_user.id:
        # User leaving organization
        if target_member.role == OrganizationRole.OWNER:
            raise HTTPException(status_code=400, detail="Owner cannot leave organization without transferring ownership")
    else:
        # Removing another user
        caller = deps.require_organization_member(db, current_user.id, organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
        if target_member.role == OrganizationRole.OWNER:
            raise HTTPException(status_code=400, detail="Cannot remove the owner")

    db.delete(target_member)
    db.commit()
    return {"message": "Member removed"}
