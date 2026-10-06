import threading
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
import json

from app.db.session import SessionLocal
from app.models.job import Job, JobExecution
from app.models.audit import AuditEvent
from app.websockets.manager import manager
import asyncio
from app.jobs import job_registry
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logger.info("Job scheduler started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            logger.info("Job scheduler stopped")

    def _run_loop(self):
        while self.running:
            try:
                self.process_jobs()
            except Exception as e:
                logger.error(f"Error in job scheduler: {e}")
            time.sleep(5)  # Poll interval

    def process_jobs(self):
        db: Session = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            
            # Recover stuck RUNNING jobs (older than 1 hour)
            stuck_jobs = db.query(Job).filter(
                Job.status == "RUNNING",
                Job.started_at < now - timedelta(hours=1)
            ).all()
            for job in stuck_jobs:
                job.status = "FAILED"
                job.failed_at = now
                job.error_message = "Job timed out"
                db.add(JobExecution(
                    job_id=job.id,
                    status="FAILED",
                    started_at=job.started_at,
                    completed_at=now,
                    error_message="Job timed out (recovered by scheduler)"
                ))
            if stuck_jobs:
                db.commit()

            # Find jobs to execute:
            # QUEUED or RETRYING where scheduled_at is null or past
            # Sort by priority desc, scheduled_at asc
            jobs_to_run = db.query(Job).filter(
                Job.status.in_(["QUEUED", "RETRYING"]),
                (Job.scheduled_at == None) | (Job.scheduled_at <= now)
            ).order_by(Job.priority.desc(), Job.scheduled_at.asc(), Job.created_at.asc()).limit(10).all()

            for job in jobs_to_run:
                self.execute_job(db, job)

        finally:
            db.close()

    def execute_job(self, db: Session, job: Job):
        now = datetime.now(timezone.utc)
        job.status = "RUNNING"
        job.started_at = now
        job.attempts += 1
        
        execution = JobExecution(
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
        ))
        db.commit()
        db.refresh(job)
        db.refresh(execution)

        handler = job_registry.get(job.job_type)
        if not handler:
            self._fail_job(db, job, execution, f"No handler registered for {job.job_type}")
            return

        try:
            payload = job.payload if job.payload else {}
            # Execute handler
            handler(payload)
            
            # Success
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
            
            # Realtime event — must never flip a successful job to failed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(manager.broadcast_to_org(job.organization_id, {
                    "type": "job.updated",
                    "entity": "job",
                    "entity_id": str(job.id)
                }))
            except Exception as broadcast_err:
                logger.warning("job.updated broadcast failed: %s", type(broadcast_err).__name__)
            
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            self._handle_job_failure(db, job, execution, str(e))
        
        db.commit()

    def _handle_job_failure(self, db: Session, job: Job, execution: JobExecution, error_message: str):
        job.error_message = error_message
        execution.error_message = error_message
        execution.completed_at = datetime.now(timezone.utc)

        if job.attempts >= job.max_attempts:
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
            # Phase 31 fix: this previously constructed Notification with
            # nonexistent columns (organization_id=, content=) and no
            # user_id, raising TypeError and crashing the scheduler loop on
            # every permanent failure. Notify the org's OWNER/ADMIN members
            # using the real schema (user_id, message).
            try:
                from app.models.notification import Notification
                from app.models.organization import OrganizationMember, OrganizationRole
                recipients = db.query(OrganizationMember).filter(
                    OrganizationMember.organization_id == job.organization_id,
                    OrganizationMember.role.in_([OrganizationRole.OWNER, OrganizationRole.ADMIN])
                ).all()
                for member in recipients:
                    db.add(Notification(
                        user_id=member.user_id,
                        type="JOB_FAILED",
                        title=f"Job {job.job_type} failed",
                        message=error_message or "Job failed",
                        entity_type="job",
                        entity_id=job.id,
                    ))
            except Exception as notify_err:
                logger.warning("job failure notification skipped: %s", type(notify_err).__name__)

            # Phase 36: also notify the rest of the org through the normal
            # notification service (preference-aware, deduplicated).
            try:
                from app.services.notification_service import notify_job_failure
                notify_job_failure(db, job.organization_id, job.id, job.job_type, error_message)
            except Exception as notify_err:
                logger.warning("phase36 job failure notification skipped: %s", type(notify_err).__name__)
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
        try:
            loop.run_until_complete(manager.broadcast_to_org(job.organization_id, {
                "type": "job.updated",
                "entity": "job",
                "entity_id": str(job.id)
            }))
        except Exception as broadcast_err:
            logger.warning("job.updated broadcast failed: %s", type(broadcast_err).__name__)

    def _fail_job(self, db: Session, job: Job, execution: JobExecution, error_message: str):
        job.status = "FAILED"
        job.error_message = error_message
        job.failed_at = datetime.now(timezone.utc)
        execution.status = "FAILED"
        execution.error_message = error_message
        execution.completed_at = job.failed_at
        db.commit()

scheduler = JobScheduler()
