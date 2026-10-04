from sqlalchemy import Column, String, DateTime, func, Uuid, JSON, Integer
import uuid
from app.db.base_class import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, index=True)
    task_name = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String, default="QUEUED", index=True) # QUEUED, RUNNING, SUCCESS, FAILED, CANCELLED
    idempotency_key = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)

class JobExecution(Base):
    __tablename__ = "job_executions"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(Uuid, nullable=False, index=True)
    status = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)
    logs = Column(String, nullable=True)
