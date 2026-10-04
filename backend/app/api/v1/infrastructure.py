from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from uuid import UUID
from app.api.deps import get_db, get_current_user, require_organization_member
from app.models.user import User
from app.models.delivery import Deployment, DeploymentStatus

router = APIRouter()

@router.get('/analytics')
def get_analytics(organization_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_organization_member(db, current_user.id, organization_id)
    # mock analytics
    total = db.query(Deployment).filter(Deployment.organization_id == organization_id).count()
    success = db.query(Deployment).filter(Deployment.organization_id == organization_id, Deployment.status == DeploymentStatus.SUCCESS).count()
    return {
        'total_deployments': total,
        'success_rate': (success / total * 100) if total > 0 else 0
    }
