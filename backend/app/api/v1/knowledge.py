from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeSpaceResponse, KnowledgeSpaceCreate, KnowledgeSpaceUpdate,
    KnowledgeDocumentResponse, KnowledgeDocumentCreate, KnowledgeDocumentUpdate, KnowledgeDocumentTreeResponse,
    KnowledgeDocumentVersionResponse, KnowledgeDocumentLinkResponse, KnowledgeDocumentLinkCreate,
    KnowledgeTagResponse, KnowledgeTagCreate, KnowledgeTagUpdate
)
from app.services import knowledge_service

router = APIRouter()

@router.get("/spaces", response_model=List[KnowledgeSpaceResponse])
def list_spaces(
    project_id: Optional[UUID] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    return knowledge_service.get_spaces(db, org_id, project_id)

@router.post("/spaces", response_model=KnowledgeSpaceResponse)
def create_space(
    space_in: KnowledgeSpaceCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    return knowledge_service.create_space(db, org_id, current_user.id, space_in)

@router.delete("/spaces/{space_id}")
def delete_space(
    space_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    knowledge_service.delete_space(db, org_id, current_user.id, space_id)
    return {"status": "ok"}

@router.get("/documents", response_model=List[KnowledgeDocumentResponse])
def list_documents(
    space_id: Optional[UUID] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    return knowledge_service.get_documents(db, org_id, space_id)

@router.post("/documents", response_model=KnowledgeDocumentResponse)
def create_document(
    doc_in: KnowledgeDocumentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    return knowledge_service.create_document(db, org_id, current_user.id, doc_in)

@router.patch("/documents/{doc_id}", response_model=KnowledgeDocumentResponse)
def update_document(
    doc_id: UUID,
    doc_in: KnowledgeDocumentUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    return knowledge_service.update_document(db, org_id, current_user.id, doc_id, doc_in)

@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    knowledge_service.delete_document(db, org_id, current_user.id, doc_id)
    return {"status": "ok"}

@router.post("/documents/{doc_id}/restore/{version_id}", response_model=KnowledgeDocumentResponse)
def restore_version(
    doc_id: UUID,
    version_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    return knowledge_service.restore_version(db, org_id, current_user.id, doc_id, version_id)

@router.post("/documents/{doc_id}/links", response_model=KnowledgeDocumentLinkResponse)
def create_link(
    doc_id: UUID,
    link_in: KnowledgeDocumentLinkCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    return knowledge_service.create_link(db, org_id, current_user.id, doc_id, link_in)
