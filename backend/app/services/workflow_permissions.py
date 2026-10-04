"""Phase 30 — Workflow permission helpers.

Bridges the Phase 17 custom RBAC system (RolePermission) with the workflow
studio endpoints. OWNER/ADMIN always pass; custom roles require the explicit
workflow permission (e.g. "workflows.publish"). MEMBER falls back to a safe
default so the existing Phase 29 behavior is preserved.
"""
from typing import Iterable, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_organization_member
from app.models.organization import OrganizationMember, OrganizationRole
from app.models.security import Role, RolePermission
from app.models.user import User
from uuid import UUID

WORKFLOW_PERMISSIONS = [
    "workflows.view",
    "workflows.create",
    "workflows.update",
    "workflows.delete",
    "workflows.publish",
    "workflows.execute",
    "workflows.simulate",
    "workflows.manage_forms",
]

# Fallback role sets used when no custom role overrides the permission.
_ROLE_FALLBACKS = {
    "workflows.view": [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER],
    "workflows.create": [OrganizationRole.OWNER, OrganizationRole.ADMIN],
    "workflows.update": [OrganizationRole.OWNER, OrganizationRole.ADMIN],
    "workflows.delete": [OrganizationRole.OWNER, OrganizationRole.ADMIN],
    "workflows.publish": [OrganizationRole.OWNER, OrganizationRole.ADMIN],
    "workflows.execute": [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER],
    "workflows.simulate": [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER],
    "workflows.manage_forms": [OrganizationRole.OWNER, OrganizationRole.ADMIN],
}


def get_workflow_permission(
    db: Session,
    user: User,
    org_id: UUID,
    permission: str = "workflows.view",
) -> OrganizationMember:
    """Require organization membership plus the given workflow permission.

    Checks the Phase 17 custom roles first so org-defined overrides win;
    otherwise falls back to the standard OWNER/ADMIN/MEMBER role sets.
    """
    member = require_organization_member(db, user.id, org_id)

    if member.role in (OrganizationRole.OWNER, OrganizationRole.ADMIN):
        return member

    # Custom role permission check (Phase 17 RBAC)
    if member.custom_role_id:
        role = db.query(Role).filter(Role.id == member.custom_role_id).first()
        if role:
            perms = [rp.permission for rp in role.permissions]
            if permission in perms:
                return member
            # If a custom role exists but lacks the permission, deny it:
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")

    # Standard-role fallback (preserves Phase 29 behavior)
    if member.role in _ROLE_FALLBACKS.get(permission, [OrganizationRole.OWNER]):
        return member

    raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
