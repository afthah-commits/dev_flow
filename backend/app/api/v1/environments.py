from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.api.deps import get_db, get_current_user, require_organization_member
from app.models.user import User
from app.models.delivery import Environment
from app.models.infrastructure import EnvironmentVariable, ServiceHealth, ServiceHealthStatus
from app.schemas.infrastructure import (
    EnvironmentVariableCreate, EnvironmentVariableUpdate, EnvironmentVariableResponse,
    ServiceHealthCreate, ServiceHealthResponse
)
from app.models.audit import AuditEvent

router = APIRouter()

@router.get('/{env_id}/health')
def get_env_health(env_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, env.organization_id)
    return {'status': env.status}

@router.post('/{env_id}/health/check')
def check_env_health(env_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, env.organization_id)
    db.add(AuditEvent(organization_id=env.organization_id, actor_user_id=current_user.id, event_type='environment.health_checked', entity_type='environment', entity_id=env.id))
    db.commit()
    return {'status': 'checked'}

@router.get('/{env_id}/variables', response_model=List[EnvironmentVariableResponse])
def get_env_vars(env_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, env.organization_id)
    vars = db.query(EnvironmentVariable).filter(EnvironmentVariable.environment_id == env_id).all()
    for v in vars:
        v.value = '********' if v.is_secret else v.encrypted_value
    return vars

@router.post('/{env_id}/variables', response_model=EnvironmentVariableResponse)
def create_env_var(env_id: UUID, var_in: EnvironmentVariableCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, env.organization_id)
    v = EnvironmentVariable(
        organization_id=env.organization_id,
        environment_id=env_id,
        key=var_in.key,
        encrypted_value=var_in.value,
        is_secret=var_in.is_secret
    )
    db.add(v)
    db.add(AuditEvent(organization_id=env.organization_id, actor_user_id=current_user.id, event_type='environment.variable_created', entity_type='environment', entity_id=env.id))
    db.commit()
    db.refresh(v)
    v.value = '********' if v.is_secret else v.encrypted_value
    return v

@router.patch('/{env_id}/variables/{var_id}', response_model=EnvironmentVariableResponse)
def update_env_var(env_id: UUID, var_id: UUID, var_in: EnvironmentVariableUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    v = db.query(EnvironmentVariable).filter(EnvironmentVariable.id == var_id, EnvironmentVariable.environment_id == env_id).first()
    if not v: raise HTTPException(404, 'Not found')
    if var_in.value is not None:
        v.encrypted_value = var_in.value
    if var_in.is_secret is not None:
        v.is_secret = var_in.is_secret
    db.add(AuditEvent(organization_id=v.organization_id, actor_user_id=current_user.id, event_type='environment.variable_updated', entity_type='environment', entity_id=env_id))
    db.commit()
    db.refresh(v)
    v.value = '********' if v.is_secret else v.encrypted_value
    return v

@router.delete('/{env_id}/variables/{var_id}')
def delete_env_var(env_id: UUID, var_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    v = db.query(EnvironmentVariable).filter(EnvironmentVariable.id == var_id, EnvironmentVariable.environment_id == env_id).first()
    if not v: raise HTTPException(404, 'Not found')
    db.delete(v)
    db.add(AuditEvent(organization_id=v.organization_id, actor_user_id=current_user.id, event_type='environment.variable_deleted', entity_type='environment', entity_id=env_id))
    db.commit()
    return {'status': 'deleted'}

@router.get('/{env_id}/services', response_model=List[ServiceHealthResponse])
def get_services(env_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, env.organization_id)
    return db.query(ServiceHealth).filter(ServiceHealth.environment_id == env_id).all()

@router.post('/{env_id}/services/check')
def check_services(env_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env: raise HTTPException(404, 'Not found')
    require_organization_member(db, current_user.id, env.organization_id)
    return {'status': 'checked'}
