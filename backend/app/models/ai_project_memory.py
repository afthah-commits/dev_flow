import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Uuid, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class AIProjectMemory(Base):
    __tablename__ = "ai_project_memories"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String, nullable=False, index=True) # architecture, technology, convention, risk, decision, goal
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    source = Column(String, nullable=True) # e.g., 'user', 'auto-detected'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    project = relationship("Project")
