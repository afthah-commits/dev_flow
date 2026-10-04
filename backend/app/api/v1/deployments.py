from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import time
import threading

from app.api.deps import get_db, get_current_user, require_organization_member
from app.models.user import User
from app.models.delivery import Deployment, DeploymentStatus
from app.models.audit import AuditEvent
from app.models.infrastructure import DeploymentApproval, DeploymentApprovalStatus
from app.schemas.delivery import DeploymentResponse
from app.schemas.infrastructure import DeploymentApprovalCreate, DeploymentApprovalResponse
from app.db.session import SessionLocal

router = APIRouter()

def mock_deployment_task(deployment_id: UUID):
    db = SessionLocal()
    try:
        dep = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not dep: return
        dep.status = DeploymentStatus.BUILDING
        db.add(AuditEvent(organization_id=dep.organization_id, event_type='deployment.started', entity_type='deployment', entity_id=dep.id))
        db.commit()
        
         # mock building
        
        dep.status = DeploymentStatus.DEPLOYING
        db.commit()
        
         # mock deploying
        
        dep.status = DeploymentStatus.SUCCESS
        db.add(AuditEvent(organization_id=dep.organization_id, event_type='deployment.success', entity_type='deployment', entity_id=dep.id))
        db.commit()
    except Exception as e:
        dep = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if dep:
            dep.status = DeploymentStatus.FAILED
            db.add(AuditEvent(organization_id=dep.organization_id, event_type='deployment.failed', entity_type='deployment', entity_id=dep.id))
            db.commit()
    finally:
        db.close()

@router.post('/{dep_id}/start')
def start_deployment(dep_id: UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dep = db.query(Deployment).filter(Deployment.id == dep_id).first()
    if not dep: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, dep.organization_id)
    background_tasks.add_task(mock_deployment_task, dep.id)
    return {'status': 'started'}

@router.post('/{dep_id}/cancel')
def cancel_deployment(dep_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dep = db.query(Deployment).filter(Deployment.id == dep_id).first()
    if not dep: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, dep.organization_id)
    dep.status = DeploymentStatus.CANCELLED
    db.add(AuditEvent(organization_id=dep.organization_id, actor_user_id=current_user.id, event_type='deployment.cancelled', entity_type='deployment', entity_id=dep.id))
    db.commit()
    return {'status': 'cancelled'}

@router.post('/{dep_id}/rollback', response_model=DeploymentResponse)
def rollback_deployment(dep_id: UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dep = db.query(Deployment).filter(Deployment.id == dep_id).first()
    if not dep: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, dep.organization_id)
    
    new_dep = Deployment(
        organization_id=dep.organization_id,
        project_id=dep.project_id,
        environment_id=dep.environment_id,
        release_id=dep.release_id,
        status=DeploymentStatus.QUEUED,
        previous_deployment_id=dep.id,
        triggered_by_id=current_user.id
    )
    db.add(new_dep)
    db.add(AuditEvent(organization_id=dep.organization_id, actor_user_id=current_user.id, event_type='deployment.rollback', entity_type='deployment', entity_id=dep.id))
    db.commit()
    db.refresh(new_dep)
    background_tasks.add_task(mock_deployment_task, new_dep.id)
    return new_dep

@router.post('/{dep_id}/approvals', response_model=DeploymentApprovalResponse)
def create_approval(dep_id: UUID, approval_in: DeploymentApprovalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dep = db.query(Deployment).filter(Deployment.id == dep_id).first()
    if not dep: raise HTTPException(404, 'Not found')
    appr = DeploymentApproval(
        organization_id=dep.organization_id,
        deployment_id=dep_id,
        requested_by_id=current_user.id,
        status=approval_in.status,
        comment=approval_in.comment
    )
    db.add(appr)
    db.commit()
    db.refresh(appr)
    return appr
