from typing import Dict, Any

with open('backend/app/api/v1/delivery.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure models are imported
if "ReleaseApproval" not in text:
    text = text.replace("from app.models.delivery import Release", "from app.models.delivery import Release, ReleaseApproval, ReleaseApprovalStatus")

new_routes = '''
@releases_router.post("/{release_id}/approvals", response_model=ReleaseApprovalResponse)
def request_approval(release_id: UUID, payload: ReleaseApprovalCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.check_permission(db, current_user.id, org_id, "manage_releases")
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    
    approval = ReleaseApproval(
        organization_id=org_id,
        release_id=release_id,
        requested_by_id=current_user.id,
        reviewer_id=payload.reviewer_id,
        comment=payload.comment,
        status=ReleaseApprovalStatus.PENDING
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    AuditEvent.log(db, org_id, current_user.id, "RELEASE_APPROVAL_REQUESTED", entity_id=release_id, entity_type="RELEASE")
    return approval

@releases_router.post("/approvals/{approval_id}/approve", response_model=ReleaseApprovalResponse)
def approve_release(approval_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    approval = db.query(ReleaseApproval).filter(ReleaseApproval.id == approval_id, ReleaseApproval.organization_id == org_id).first()
    if not approval: raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.reviewer_id != current_user.id:
        deps.check_permission(db, current_user.id, org_id, "manage_releases")
        
    approval.status = ReleaseApprovalStatus.APPROVED
    
    release = db.query(Release).filter(Release.id == approval.release_id).first()
    if release:
        release.status = ReleaseStatus.APPROVED
        release.approved_by_id = current_user.id
        
    db.commit()
    db.refresh(approval)
    
    AuditEvent.log(db, org_id, current_user.id, "RELEASE_APPROVED", entity_id=approval.release_id, entity_type="RELEASE")
    return approval

@releases_router.post("/approvals/{approval_id}/reject", response_model=ReleaseApprovalResponse)
def reject_release(approval_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    approval = db.query(ReleaseApproval).filter(ReleaseApproval.id == approval_id, ReleaseApproval.organization_id == org_id).first()
    if not approval: raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.reviewer_id != current_user.id:
        deps.check_permission(db, current_user.id, org_id, "manage_releases")
        
    approval.status = ReleaseApprovalStatus.REJECTED
    
    release = db.query(Release).filter(Release.id == approval.release_id).first()
    if release:
        release.status = ReleaseStatus.READY
        
    db.commit()
    db.refresh(approval)
    
    AuditEvent.log(db, org_id, current_user.id, "RELEASE_REJECTED", entity_id=approval.release_id, entity_type="RELEASE")
    return approval

@releases_router.post("/approvals/{approval_id}/revoke", response_model=ReleaseApprovalResponse)
def revoke_approval(approval_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    approval = db.query(ReleaseApproval).filter(ReleaseApproval.id == approval_id, ReleaseApproval.organization_id == org_id).first()
    if not approval: raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.requested_by_id != current_user.id:
        deps.check_permission(db, current_user.id, org_id, "manage_releases")
        
    approval.status = ReleaseApprovalStatus.REVOKED
    db.commit()
    db.refresh(approval)
    
    AuditEvent.log(db, org_id, current_user.id, "RELEASE_APPROVAL_REVOKED", entity_id=approval.release_id, entity_type="RELEASE")
    return approval

@environments_router.get("/{env_id}/health")
def get_environment_health(env_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    env = db.query(Environment).filter(Environment.id == env_id, Environment.organization_id == org_id).first()
    if not env: raise HTTPException(status_code=404, detail="Environment not found")
    
    status = ReleaseEngine.check_environment_health(db, str(env.id))
    return {"status": status}

@releases_router.post("/{release_id}/promote", response_model=ReleaseResponse)
def promote_release(release_id: UUID, target_env: str, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.check_permission(db, current_user.id, org_id, "manage_releases")
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    
    # Simple promote logic: just change target environment
    release.target_environment = target_env
    release.status = ReleaseStatus.READY
    db.commit()
    db.refresh(release)
    
    AuditEvent.log(db, org_id, current_user.id, "RELEASE_PROMOTED", entity_id=release.id, entity_type="RELEASE", details={"target_env": target_env})
    return release

@releases_router.post("/{release_id}/rollback", response_model=ReleaseResponse)
def rollback_release(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.check_permission(db, current_user.id, org_id, "manage_releases")
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    
    release.status = ReleaseStatus.ROLLED_BACK
    from datetime import datetime
    import pytz
    release.rollback_timestamp = datetime.now(pytz.utc)
    db.commit()
    db.refresh(release)
    
    AuditEvent.log(db, org_id, current_user.id, "RELEASE_ROLLED_BACK", entity_id=release.id, entity_type="RELEASE")
    return release
'''

text += new_routes

with open('backend/app/api/v1/delivery.py', 'w', encoding='utf-8') as f:
    f.write(text)
