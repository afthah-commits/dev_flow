from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.api.deps import get_db, get_current_user, require_organization_member
from app.models.user import User
from app.models.infrastructure import DeploymentIncident, DeploymentIncidentStatus
from app.schemas.infrastructure import DeploymentIncidentCreate, DeploymentIncidentUpdate, DeploymentIncidentResponse
from app.models.audit import AuditEvent

router = APIRouter()

@router.get('/{incident_id}', response_model=DeploymentIncidentResponse)
def get_incident(incident_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inc = db.query(DeploymentIncident).filter(DeploymentIncident.id == incident_id).first()
    if not inc: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, inc.organization_id)
    return inc

@router.post('', response_model=DeploymentIncidentResponse)
def create_incident(inc_in: DeploymentIncidentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # organization_id is determined from environment_id
    from app.models.delivery import Environment
    env = db.query(Environment).filter(Environment.id == inc_in.environment_id).first()
    if not env: raise HTTPException(404, 'Environment not found')
    require_organization_member(db, current_user.id, env.organization_id)
    inc = DeploymentIncident(
        organization_id=env.organization_id,
        environment_id=inc_in.environment_id,
        deployment_id=inc_in.deployment_id,
        severity=inc_in.severity,
        title=inc_in.title,
        description=inc_in.description,
        status=inc_in.status
    )
    db.add(inc)
    db.add(AuditEvent(organization_id=env.organization_id, actor_user_id=current_user.id, event_type='incident.created', entity_type='incident'))
    db.commit()
    db.refresh(inc)
    return inc

@router.patch('/{incident_id}', response_model=DeploymentIncidentResponse)
def update_incident(incident_id: UUID, inc_in: DeploymentIncidentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inc = db.query(DeploymentIncident).filter(DeploymentIncident.id == incident_id).first()
    if not inc: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, inc.organization_id)
    for k, v in inc_in.model_dump(exclude_unset=True).items():
        setattr(inc, k, v)
    if inc_in.status == DeploymentIncidentStatus.RESOLVED:
        from datetime import datetime
        import pytz
        inc.resolved_at = datetime.now(pytz.utc)
    db.add(AuditEvent(organization_id=inc.organization_id, actor_user_id=current_user.id, event_type='incident.updated', entity_type='incident', entity_id=inc.id))
    db.commit()
    db.refresh(inc)
    return inc
