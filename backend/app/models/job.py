from sqlalchemy import Column, String, DateTime, func, Uuid, JSON, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String, nullable=False, index=True)
    status = Column(String, default="QUEUED", index=True) # QUEUED, RUNNING, SUCCESS, FAILED, RETRYING, CANCELLED
    payload = Column(JSON, nullable=True)
    priority = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)
    idempotency_key = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")

class JobExecution(Base):
    __tablename__ = "job_executions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(Uuid, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)
    logs = Column(String, nullable=True)
    
    job = relationship("Job", back_populates="executions")

class JobSchedule(Base):
    __tablename__ = "job_schedules"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    job_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    cron_expression = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
