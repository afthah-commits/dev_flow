import uuid
from sqlalchemy import Column, String, Date, DateTime, func, ForeignKey, Uuid, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    author_user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    
    completed_tasks = Column(JSON, nullable=False, default=list)
    next_plan = Column(JSON, nullable=False, default=list)
    blockers = Column(JSON, nullable=False, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('organization_id', 'author_user_id', 'report_date', name='uq_daily_report_org_user_date'),
    )
    
    author = relationship("User", foreign_keys=[author_user_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
