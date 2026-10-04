import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Uuid, Enum, Boolean, Integer, Table, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class DocumentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class SpaceVisibility(str, enum.Enum):
    PRIVATE = "PRIVATE"
    TEAM = "TEAM"
    ORGANIZATION = "ORGANIZATION"
    CLIENTS = "CLIENTS"
    PUBLIC = "PUBLIC"

class EntityType(str, enum.Enum):
    PROJECT = "PROJECT"
    TASK = "TASK"
    SPRINT = "SPRINT"
    MILESTONE = "MILESTONE"
    RELEASE = "RELEASE"
    DISCUSSION = "DISCUSSION"

document_tags = Table(
    "knowledge_document_tags",
    Base.metadata,
    Column("document_id", Uuid, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Uuid, ForeignKey("knowledge_tags.id", ondelete="CASCADE"), primary_key=True)
)

class KnowledgeTag(Base):
    __tablename__ = "knowledge_tags"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('organization_id', 'name', name='uq_knowledge_tag_name'),)

class KnowledgeSpace(Base):
    __tablename__ = "knowledge_spaces"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    visibility = Column(Enum(SpaceVisibility, native_enum=False), default=SpaceVisibility.ORGANIZATION, nullable=False)
    created_by = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    documents = relationship("KnowledgeDocument", back_populates="space", cascade="all, delete-orphan")

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    space_id = Column(Uuid, ForeignKey("knowledge_spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Uuid, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=True)
    content_format = Column(String, default="markdown", nullable=False)
    status = Column(Enum(DocumentStatus, native_enum=False), default=DocumentStatus.DRAFT, nullable=False, index=True)
    created_by = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_pinned = Column(Boolean, default=False, nullable=False)

    space = relationship("KnowledgeSpace", back_populates="documents")
    parent = relationship("KnowledgeDocument", remote_side=[id], back_populates="children")
    children = relationship("KnowledgeDocument", back_populates="parent")
    versions = relationship("KnowledgeDocumentVersion", back_populates="document", cascade="all, delete-orphan", order_by="desc(KnowledgeDocumentVersion.version_number)")
    tags = relationship("KnowledgeTag", secondary=document_tags)
    links = relationship("KnowledgeDocumentLink", back_populates="document", cascade="all, delete-orphan")
    watchers = relationship("KnowledgeDocumentWatcher", back_populates="document", cascade="all, delete-orphan")

class KnowledgeDocumentVersion(Base):
    __tablename__ = "knowledge_document_versions"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(Uuid, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    change_summary = Column(String, nullable=True)
    created_by = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("KnowledgeDocument", back_populates="versions")
    __table_args__ = (UniqueConstraint('document_id', 'version_number', name='uq_doc_version_num'),)

class KnowledgeDocumentLink(Base):
    __tablename__ = "knowledge_document_links"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(Uuid, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(Enum(EntityType, native_enum=False), nullable=False)
    entity_id = Column(Uuid, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("KnowledgeDocument", back_populates="links")
    __table_args__ = (UniqueConstraint('document_id', 'entity_type', 'entity_id', name='uq_doc_link'),)

class KnowledgeDocumentWatcher(Base):
    __tablename__ = "knowledge_document_watchers"
    document_id = Column(Uuid, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("KnowledgeDocument", back_populates="watchers")
