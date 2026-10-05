from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.audit import AuditEvent
from app.models.organization import OrganizationMember
from sqlalchemy import func

router = APIRouter()

@router.get("/system")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Phase 31: this endpoint previously aggregated jobs and security events
    # across ALL organizations for any authenticated user. Scope it to the
    # organizations the caller actually belongs to.
    org_ids = [
        m.organization_id
        for m in db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .all()
    ]
    if not org_ids:
        raise HTTPException(status_code=403, detail="You are not a member of any organization")

    # Jobs (scoped to caller's organizations)
    queued_jobs = db.query(Job).filter(Job.status == 'QUEUED', Job.organization_id.in_(org_ids)).count()
    running_jobs = db.query(Job).filter(Job.status == 'RUNNING', Job.organization_id.in_(org_ids)).count()
    failed_jobs = db.query(Job).filter(Job.status == 'FAILED', Job.organization_id.in_(org_ids)).count()

    # Audit Events (Security) — org-scoped only; NULL-org events excluded
    recent_security_events = (
        db.query(AuditEvent)
        .filter(AuditEvent.organization_id.in_(org_ids))
        .order_by(AuditEvent.created_at.desc())
        .limit(10)
        .all()
    )
    
    # API Performance (Stubbed for now from MemoryCacheProvider or log aggregation)
    
    return {
        "health": {
            "database": "healthy",
            "workers": "healthy",
            "integrations": "healthy"
        },
        "jobs": {
            "queued": queued_jobs,
            "running": running_jobs,
            "failed": failed_jobs
        },
        "performance": {
            "average_latency_ms": 45,
            "error_rate_pct": 0.2,
            "requests_per_minute": 120
        },
        "recent_security_events": [
            {
                "id": str(e.id),
                "type": e.event_type,
                "created_at": e.created_at,
                "actor": str(e.actor_user_id) if e.actor_user_id else None
            } for e in recent_security_events
        ]
    }
