import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Uuid, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class GitHubConnection(Base):
    __tablename__ = "github_connections"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    github_user_id = Column(String, nullable=False, unique=True, index=True)
    github_username = Column(String, nullable=False)
    github_avatar_url = Column(String, nullable=True)
    access_token_encrypted = Column(Text, nullable=False)
    token_type = Column(String, nullable=True)
    scopes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="github_connection")


class ProjectGitHubRepository(Base):
    __tablename__ = "project_github_repositories"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    github_repository_id = Column(String, nullable=False)
    github_owner = Column(String, nullable=False)
    github_name = Column(String, nullable=False)
    github_full_name = Column(String, nullable=False)
    github_url = Column(String, nullable=False)
    default_branch = Column(String, nullable=True)
    private = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    project = relationship("Project", back_populates="github_repository")
