import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    actor_user_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String, nullable=True, index=True)
    entity_type = Column(String, nullable=True, index=True)
    entity_id = Column(Uuid, nullable=True, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    team_id = Column(Uuid, ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    metadata_ = Column("metadata", JSON, nullable=True) # use metadata_ to avoid conflict with Base.metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    organization = relationship("Organization")
    actor = relationship("User")
    project = relationship("Project")
    team = relationship("Team")
