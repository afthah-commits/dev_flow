from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from uuid import UUID
import uuid

from app.api import deps
from app.models.user import User
from app.models.organization import OrganizationRole, OrganizationMember
from app.models.security import RolePermission, Role, LoginEvent, UserSession
from app.models.audit import AuditEvent
from app.models.governance import (
    OrganizationSecurityPolicy, OrganizationDomain, 
    OrganizationIdentityProvider, DataExportJob, SecurityApproval, OrganizationDeletionRequest
)
from app.schemas.governance import (
    OrganizationSecurityPolicyUpdate, OrganizationSecurityPolicyResponse,
    OrganizationDomainCreate, OrganizationDomainResponse,
    DataExportJobCreate, DataExportJobResponse
)

router = APIRouter()

def check_permission(db: Session, member: OrganizationMember, required_permission: str):
    if member.role in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
        return True
    if member.custom_role_id:
        role = db.query(Role).filter(Role.id == member.custom_role_id).first()
        if role:
            perms = [rp.permission for rp in role.permissions]
            if required_permission in perms:
                return True
    raise HTTPException(status_code=403, detail="Not authorized")

@router.get("/security-policy", response_model=OrganizationSecurityPolicyResponse)
def get_security_policy(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "security.view")
    
    policy = db.query(OrganizationSecurityPolicy).filter(OrganizationSecurityPolicy.organization_id == str(org_id)).first()
    if not policy:
        policy = OrganizationSecurityPolicy(organization_id=str(org_id))
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy

@router.patch("/security-policy", response_model=OrganizationSecurityPolicyResponse)
def update_security_policy(
    policy_in: OrganizationSecurityPolicyUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "security.manage")
    
    policy = db.query(OrganizationSecurityPolicy).filter(OrganizationSecurityPolicy.organization_id == str(org_id)).first()
    if not policy:
        policy = OrganizationSecurityPolicy(organization_id=str(org_id))
        db.add(policy)
        db.commit()
        
    update_data = policy_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
        
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="security.policy_updated", organization_id=org_id))
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

@router.get("/domains", response_model=List[OrganizationDomainResponse])
def get_domains(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "security.view")
    
    domains = db.query(OrganizationDomain).filter(OrganizationDomain.organization_id == str(org_id)).all()
    return domains

@router.post("/domains", response_model=OrganizationDomainResponse)
def add_domain(
    domain_in: OrganizationDomainCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "security.manage")
    
    domain = OrganizationDomain(
        organization_id=str(org_id),
        domain=domain_in.domain,
        verification_token=f"devflow-verify-{uuid.uuid4()}"
    )
    db.add(domain)
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="security.domain_added", organization_id=org_id))
    db.commit()
    db.refresh(domain)
    return domain

@router.post("/domains/{domain_id}/verify")
def verify_domain(
    domain_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "security.manage")
    
    domain = db.query(OrganizationDomain).filter(
        OrganizationDomain.id == domain_id, 
        OrganizationDomain.organization_id == str(org_id)
    ).first()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
        
    from datetime import datetime, timezone
    domain.verified_at = datetime.now(timezone.utc)
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="security.domain_verified", organization_id=org_id))
    db.commit()
    return {"success": True, "message": "Domain verified (MOCK)"}

@router.delete("/domains/{domain_id}")
def delete_domain(
    domain_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "security.manage")
    
    domain = db.query(OrganizationDomain).filter(
        OrganizationDomain.id == domain_id, 
        OrganizationDomain.organization_id == str(org_id)
    ).first()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
        
    db.delete(domain)
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="security.domain_deleted", organization_id=org_id))
    db.commit()
    return {"success": True}

@router.post("/data-exports", response_model=DataExportJobResponse)
def request_export(
    export_in: DataExportJobCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "exports.create")
    
    job = DataExportJob(
        organization_id=str(org_id),
        requested_by_id=str(current_user.id),
        export_type=export_in.export_type
    )
    db.add(job)
    db.add(AuditEvent(actor_user_id=current_user.id, event_type="security.export_requested", organization_id=org_id))
    db.commit()
    db.refresh(job)
    return job

@router.get("/data-exports", response_model=List[DataExportJobResponse])
def get_exports(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "exports.view")
    
    jobs = db.query(DataExportJob).filter(DataExportJob.organization_id == str(org_id)).all()
    return jobs

@router.get("/compliance/overview")
def get_compliance_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header required")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "security.view")
    
    # Generate compliance aggregations securely without N+1
    total_members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).count()
    failed_logins = db.query(LoginEvent).filter(LoginEvent.organization_id == org_id, LoginEvent.success == False).count()
    
    # In a real app we would join Users with Members to check MFA status
    
    return {
        "mfa_adoption": 100, 
        "total_members": total_members,
        "recent_failed_logins": failed_logins,
        "security_score": 85
    }

