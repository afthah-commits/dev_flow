from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.knowledge import DocumentStatus, SpaceVisibility, EntityType

# TAGS
class KnowledgeTagBase(BaseModel):
    name: str
    color: Optional[str] = None

class KnowledgeTagCreate(KnowledgeTagBase):
    pass

class KnowledgeTagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

class KnowledgeTagResponse(KnowledgeTagBase):
    id: UUID
    organization_id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

# SPACES
class KnowledgeSpaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    visibility: SpaceVisibility = SpaceVisibility.ORGANIZATION
    project_id: Optional[UUID] = None

class KnowledgeSpaceCreate(KnowledgeSpaceBase):
    pass

class KnowledgeSpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[SpaceVisibility] = None
    project_id: Optional[UUID] = None

class KnowledgeSpaceResponse(KnowledgeSpaceBase):
    id: UUID
    organization_id: UUID
    slug: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# DOCUMENT LINKS
class KnowledgeDocumentLinkBase(BaseModel):
    entity_type: EntityType
    entity_id: UUID

class KnowledgeDocumentLinkCreate(KnowledgeDocumentLinkBase):
    pass

class KnowledgeDocumentLinkResponse(KnowledgeDocumentLinkBase):
    id: UUID
    document_id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

# DOCUMENT VERSIONS
class KnowledgeDocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    title: str
    content: Optional[str] = None
    change_summary: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    class Config:
        from_attributes = True

# DOCUMENTS
class KnowledgeDocumentBase(BaseModel):
    title: str
    space_id: UUID
    parent_id: Optional[UUID] = None
    content: Optional[str] = None
    content_format: str = "markdown"
    status: DocumentStatus = DocumentStatus.DRAFT
    is_pinned: bool = False

class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    tags: Optional[List[UUID]] = None

class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    parent_id: Optional[UUID] = None
    content: Optional[str] = None
    content_format: Optional[str] = None
    status: Optional[DocumentStatus] = None
    is_pinned: Optional[bool] = None
    tags: Optional[List[UUID]] = None
    change_summary: Optional[str] = None

class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    id: UUID
    organization_id: UUID
    slug: str
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[KnowledgeTagResponse] = []
    links: List[KnowledgeDocumentLinkResponse] = []
    
    class Config:
        from_attributes = True

class KnowledgeDocumentTreeResponse(KnowledgeDocumentResponse):
    children: List['KnowledgeDocumentTreeResponse'] = []

KnowledgeDocumentTreeResponse.model_rebuild()
