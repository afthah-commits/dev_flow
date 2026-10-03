import os

file_path = "c:/personal_projects/devflow/backend/app/api/deps.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

helpers = """
from app.models.organization import OrganizationMember, OrganizationRole
from fastapi import Header
from typing import Optional

def get_current_organization_id(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id")
) -> Optional[UUID]:
    if not x_organization_id:
        return None
    try:
        return UUID(x_organization_id)
    except ValueError:
        return None

def require_organization_member(
    db: Session, user_id: UUID, organization_id: UUID, allowed_roles: list[OrganizationRole] = None
) -> OrganizationMember:
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
        
    if allowed_roles and member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required role in this organization"
        )
        
    return member
"""

if "require_organization_member" not in content:
    content = content + "\n" + helpers
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
print("deps.py updated")
