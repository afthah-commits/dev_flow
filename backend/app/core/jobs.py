import asyncio
import logging
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.job import Job, JobExecution
import traceback

logger = logging.getLogger(__name__)

class BackgroundJobEngine:
    def __init__(self):
        self.registry: Dict[str, Callable] = {}
        self._running = False
        self._task = None

    def register(self, task_name: str, handler: Callable):
        self.registry[task_name] = handler

    async def _execute_job(self, db: Session, job: Job):
        handler = self.registry.get(job.task_name)
        if not handler:
            job.status = "FAILED"
            job.error_message = f"Handler for {job.task_name} not found"
            db.commit()
            return

        execution = JobExecution(job_id=job.id, status="RUNNING")
        db.add(execution)
        
        job.status = "RUNNING"
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(execution)

        try:
            # We assume handlers are async
            if asyncio.iscoroutinefunction(handler):
                await handler(job.payload)
            else:
                handler(job.payload)
            
            job.status = "SUCCESS"
            job.completed_at = datetime.now(timezone.utc)
            execution.status = "SUCCESS"
            execution.completed_at = job.completed_at
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Job {job.id} failed: {error_trace}")
            
            job.status = "FAILED"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            
            execution.status = "FAILED"
            execution.error_message = str(e)
            execution.logs = error_trace
            execution.completed_at = job.completed_at
            
        finally:
            db.commit()

    async def _loop(self):
        while self._running:
            db = SessionLocal()
            try:
                # Find queued jobs
                now = datetime.now(timezone.utc)
                jobs = db.query(Job).filter(
                    Job.status == "QUEUED",
                    (Job.next_run_at == None) | (Job.next_run_at <= now)
                ).limit(10).all()
                
                for job in jobs:
                    await self._execute_job(db, job)
                    
            except Exception as e:
                logger.error(f"Error in job engine loop: {e}")
            finally:
                db.close()
                
            await asyncio.sleep(2)  # poll every 2 seconds

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

job_engine = BackgroundJobEngine()

def enqueue_job(db: Session, name: str, task_name: str, payload: dict, idempotency_key: Optional[str] = None):
    if idempotency_key:
        existing = db.query(Job).filter(Job.idempotency_key == idempotency_key).first()
        if existing:
            return existing
            
    job = Job(
        name=name,
        task_name=task_name,
        payload=payload,
        idempotency_key=idempotency_key,
        status="QUEUED"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
