import re

with open(r"app/jobs/scheduler.py", "r", encoding="utf-8") as f:
    content = f.read()

patch_audit_import = """from app.models.audit import AuditEvent
from app.websockets.manager import manager
import asyncio"""

if "AuditEvent" not in content:
    content = content.replace("from app.jobs import job_registry", patch_audit_import + "\nfrom app.jobs import job_registry")

# Let's replace the execution success block
success_search = """            # Success
            job.status = "SUCCESS"
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = None
            execution.status = "SUCCESS"
            execution.completed_at = job.completed_at"""

success_replacement = """            # Success
            job.status = "SUCCESS"
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = None
            execution.status = "SUCCESS"
            execution.completed_at = job.completed_at
            
            db.add(AuditEvent(
                organization_id=job.organization_id,
                event_type="job.completed",
                entity_type="job",
                entity_id=job.id,
                metadata_={"job_type": job.job_type}
            ))
            
            # Realtime event
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(manager.broadcast_to_org(job.organization_id, {
                "type": "job.updated",
                "entity": "job",
                "entity_id": str(job.id)
            }))"""
content = content.replace(success_search, success_replacement)

# Let's replace _handle_job_failure
failure_search = """        if job.attempts >= job.max_attempts:
            job.status = "FAILED"
            job.failed_at = datetime.now(timezone.utc)
            execution.status = "FAILED"
            
            # Emit notification if necessary, but keep it decoupled
        else:
            job.status = "RETRYING"
            # Exponential backoff: 2^attempts * 10 seconds
            delay = (2 ** job.attempts) * 10
            job.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            execution.status = "FAILED\""""

failure_replacement = """        if job.attempts >= job.max_attempts:
            job.status = "FAILED"
            job.failed_at = datetime.now(timezone.utc)
            execution.status = "FAILED"
            
            db.add(AuditEvent(
                organization_id=job.organization_id,
                event_type="job.permanently_failed",
                entity_type="job",
                entity_id=job.id,
                metadata_={"job_type": job.job_type, "error": error_message}
            ))
            from app.models.notification import Notification
            db.add(Notification(
                organization_id=job.organization_id,
                type="JOB_FAILED",
                title=f"Job {job.job_type} failed",
                content=error_message,
                entity_type="job",
                entity_id=job.id
            ))
        else:
            job.status = "RETRYING"
            delay = (2 ** job.attempts) * 10
            job.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            execution.status = "FAILED"
            
            db.add(AuditEvent(
                organization_id=job.organization_id,
                event_type="job.failed",
                entity_type="job",
                entity_id=job.id,
                metadata_={"job_type": job.job_type, "error": error_message, "will_retry": True}
            ))
            
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(manager.broadcast_to_org(job.organization_id, {
            "type": "job.updated",
            "entity": "job",
            "entity_id": str(job.id)
        }))"""
content = content.replace(failure_search, failure_replacement)

# And let's replace start of execute_job
start_search = """        execution = JobExecution(
            job_id=job.id,
            status="RUNNING",
            started_at=now
        )
        db.add(execution)"""
start_replace = """        execution = JobExecution(
            job_id=job.id,
            status="RUNNING",
            started_at=now
        )
        db.add(execution)
        db.add(AuditEvent(
            organization_id=job.organization_id,
            event_type="job.started",
            entity_type="job",
            entity_id=job.id,
            metadata_={"job_type": job.job_type, "attempt": job.attempts}
        ))"""
content = content.replace(start_search, start_replace)

with open(r"app/jobs/scheduler.py", "w", encoding="utf-8") as f:
    f.write(content)
print("done")
