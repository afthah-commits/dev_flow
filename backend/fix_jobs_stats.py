import re

with open(r"app/api/v1/jobs.py", "r", encoding="utf-8") as f:
    content = f.read()

new_stats_func = """@router.get("/stats")
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
"""

start_idx = content.find('@router.get("/stats")')
if start_idx != -1:
    end_idx = content.find('@router.get("/{job_id}")', start_idx)
    if end_idx != -1:
        content = content[:start_idx] + new_stats_func + "\n" + content[end_idx:]
    else:
        content = content[:start_idx] + new_stats_func

with open(r"app/api/v1/jobs.py", "w", encoding="utf-8") as f:
    f.write(content)
print("done")
