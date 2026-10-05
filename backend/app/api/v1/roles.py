from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user, require_organization_member
from app.models.user import User
from app.models.security import Role, RolePermission
from app.models.organization import OrganizationRole

router = APIRouter()

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str]

class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_system_role: bool
    permissions: List[str]

    class Config:
        from_attributes = True

@router.get("/{organization_id}/roles", response_model=List[RoleResponse])
def get_roles(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_organization_member(db, current_user.id, organization_id)
    roles = db.query(Role).filter(Role.organization_id == organization_id).all()
    
    result = []
    for role in roles:
        perms = [rp.permission for rp in role.permissions]
        result.append(RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system_role=role.is_system_role,
            permissions=perms
        ))
    return result

@router.post("/{organization_id}/roles", response_model=RoleResponse)
def create_role(
    organization_id: UUID,
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    member = require_organization_member(db, current_user.id, organization_id)
    if member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to create roles")
        
    role = Role(
        organization_id=organization_id,
        name=role_in.name,
        description=role_in.description,
        is_system_role=False
    )
    db.add(role)
    db.flush()
    
    for p in role_in.permissions:
        db.add(RolePermission(role_id=role.id, permission=p))
        
    db.commit()
    db.refresh(role)
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        is_system_role=role.is_system_role,
        permissions=role_in.permissions
    )

@router.delete("/{organization_id}/roles/{role_id}", status_code=204)
def delete_role(
    organization_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    member = require_organization_member(db, current_user.id, organization_id)
    if member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to delete roles")
        
    role = db.query(Role).filter(Role.id == role_id, Role.organization_id == organization_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    if role.is_system_role:
        raise HTTPException(status_code=400, detail="Cannot delete system role")
        
    db.delete(role)
    db.commit()
