from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.audit import AuditEvent
from sqlalchemy import func

router = APIRouter()

@router.get("/system")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # For now, just require user to be active
    # In a real app we would check a global SUPERADMIN flag
    
    # Jobs
    queued_jobs = db.query(Job).filter(Job.status == 'QUEUED').count()
    running_jobs = db.query(Job).filter(Job.status == 'RUNNING').count()
    failed_jobs = db.query(Job).filter(Job.status == 'FAILED').count()
    
    # Audit Events (Security)
    recent_security_events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(10).all()
    
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
