from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
import json

from app.db.session import SessionLocal
from app.api import deps
from app.models.job import Job, JobExecution
from app.models.user import User

router = APIRouter()

@router.get("")
def list_jobs(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    job_type: Optional[str] = None
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id)
    
    query = db.query(Job).filter(Job.organization_id == organization_id)
    
    if status:
        query = query.filter(Job.status == status)
    if job_type:
        query = query.filter(Job.job_type == job_type)
        
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    
    # manual serialization since schema might not exist
    result = []
    for job in jobs:
        result.append({
            "id": str(job.id),
            "organization_id": str(job.organization_id),
            "job_type": job.job_type,
            "status": job.status,
            "payload": job.payload,
            "priority": job.priority,
            "attempts": job.attempts,
            "max_attempts": job.max_attempts,
            "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "failed_at": job.failed_at.isoformat() if job.failed_at else None,
            "error_message": job.error_message,
            "idempotency_key": job.idempotency_key,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None
        })
    return result

@router.get("/stats")
def get_job_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id)
    
    from sqlalchemy import func
    
    status_counts = db.query(Job.status, func.count(Job.id)).filter(
        Job.organization_id == organization_id
    ).group_by(Job.status).all()
    
    stats = {
        "QUEUED": 0,
        "RUNNING": 0,
        "SUCCESS": 0,
        "FAILED": 0,
        "RETRYING": 0,
        "CANCELLED": 0,
        "total": 0
    }
    
    for status, count in status_counts:
        if status in stats:
            stats[status] = count
        stats["total"] += count
        
    avg_time = db.query(func.avg(
        func.julianday(Job.completed_at) - func.julianday(Job.started_at)
    )).filter(
        Job.organization_id == organization_id,
        Job.status == "SUCCESS",
        Job.started_at.isnot(None),
        Job.completed_at.isnot(None)
    ).scalar()
    
    from datetime import datetime, timedelta, timezone
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    
    throughput = db.query(func.count(Job.id)).filter(
        Job.organization_id == organization_id,
        Job.status == "SUCCESS",
        Job.completed_at >= yesterday
    ).scalar() or 0
    
    failed_24h = db.query(func.count(Job.id)).filter(
        Job.organization_id == organization_id,
        Job.status == "FAILED",
        Job.failed_at >= yesterday
    ).scalar() or 0
    
    total_24h = throughput + failed_24h
    success_rate = (throughput / total_24h * 100) if total_24h > 0 else 0
    failure_rate = (failed_24h / total_24h * 100) if total_24h > 0 else 0
    
    avg_time_sec = (avg_time * 86400) if avg_time else 0
    
    stats.update({
        "throughput_24h": throughput,
        "success_rate_24h": round(success_rate, 2),
        "failure_rate_24h": round(failure_rate, 2),
        "avg_execution_time_sec": round(avg_time_sec, 2),
        "queue_depth": stats["QUEUED"] + stats["RETRYING"]
    })
    
    return stats

@router.get("/{job_id}")
def get_job(
    job_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id)
    job = db.query(Job).filter(Job.id == job_id, Job.organization_id == organization_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "id": str(job.id),
        "organization_id": str(job.organization_id),
        "job_type": job.job_type,
        "status": job.status,
        "payload": job.payload,
        "priority": job.priority,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "failed_at": job.failed_at.isoformat() if job.failed_at else None,
        "error_message": job.error_message,
        "idempotency_key": job.idempotency_key,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None
    }

@router.get("/{job_id}/executions")
def get_job_executions(
    job_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id),
    skip: int = 0,
    limit: int = 100
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id)
    job = db.query(Job).filter(Job.id == job_id, Job.organization_id == organization_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    executions = db.query(JobExecution).filter(JobExecution.job_id == job_id).order_by(JobExecution.started_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for exec in executions:
        result.append({
            "id": str(exec.id),
            "job_id": str(exec.job_id),
            "status": exec.status,
            "started_at": exec.started_at.isoformat() if exec.started_at else None,
            "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
            "error_message": exec.error_message,
            "logs": exec.logs
        })
    return result

@router.post("/{job_id}/retry")
def retry_job(
    job_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id)
    job = db.query(Job).filter(Job.id == job_id, Job.organization_id == organization_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status not in ["FAILED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Only failed or cancelled jobs can be retried")
        
    job.status = "QUEUED"
    job.attempts = 0
    job.error_message = None
    job.scheduled_at = datetime.now(timezone.utc)
    
    from app.models.audit import AuditEvent
    db.add(AuditEvent(
        organization_id=organization_id,
        actor_user_id=current_user.id,
        event_type="job.retry",
        entity_type="job",
        entity_id=job.id,
        metadata_={"job_type": job.job_type}
    ))
    
    db.commit()
    return {"status": "success", "message": "Job queued for retry"}

@router.post("/{job_id}/cancel")
def cancel_job(
    job_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    organization_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id)
    job = db.query(Job).filter(Job.id == job_id, Job.organization_id == organization_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status not in ["QUEUED", "RETRYING"]:
        raise HTTPException(status_code=400, detail="Only queued or retrying jobs can be cancelled")
        
    job.status = "CANCELLED"
    job.error_message = "Cancelled by user"
    
    from app.models.audit import AuditEvent
    db.add(AuditEvent(
        organization_id=organization_id,
        actor_user_id=current_user.id,
        event_type="job.cancelled",
        entity_type="job",
        entity_id=job.id,
        metadata_={"job_type": job.job_type}
    ))
    
    db.commit()
    return {"status": "success", "message": "Job cancelled"}
