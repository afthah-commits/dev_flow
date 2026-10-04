from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.db.base_class import Base

class ReportType(str, enum.Enum):
    PROJECT_OVERVIEW = "PROJECT_OVERVIEW"
    TASK_ANALYTICS = "TASK_ANALYTICS"
    SPRINT_REPORT = "SPRINT_REPORT"
    TEAM_WORKLOAD = "TEAM_WORKLOAD"
    TIME_TRACKING = "TIME_TRACKING"
    PRODUCTIVITY = "PRODUCTIVITY"
    GITHUB_DELIVERY = "GITHUB_DELIVERY"
    RELEASE_DELIVERY = "RELEASE_DELIVERY"
    AUDIT_ACTIVITY = "AUDIT_ACTIVITY"
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    configuration = Column(JSON, nullable=False, default=dict)
    
    created_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization")
    created_by = relationship("User")

