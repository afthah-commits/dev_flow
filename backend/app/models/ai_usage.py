import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class AIUsage(Base):
    __tablename__ = "ai_usages"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    provider = Column(String, nullable=False) # 'mock', 'openai', etc.
    model = Column(String, nullable=False)
    request_type = Column(String, nullable=False) # e.g., 'project_summary', 'chat'
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization")
    user = relationship("User")
