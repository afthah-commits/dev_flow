import uuid
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
import re

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


from app.models.knowledge import KnowledgeSpace, KnowledgeDocument, KnowledgeDocumentVersion, KnowledgeTag, KnowledgeDocumentLink, KnowledgeDocumentWatcher, DocumentStatus
from app.models.project import Project
from app.schemas.knowledge import KnowledgeSpaceCreate, KnowledgeSpaceUpdate, KnowledgeDocumentCreate, KnowledgeDocumentUpdate, KnowledgeDocumentLinkCreate, KnowledgeTagCreate
from app.services.audit_service import record_event

def get_spaces(db: Session, org_id: UUID, project_id: Optional[UUID] = None) -> List[KnowledgeSpace]:
    query = db.query(KnowledgeSpace).filter(KnowledgeSpace.organization_id == org_id)
    if project_id:
        query = query.filter(KnowledgeSpace.project_id == project_id)
    return query.all()

def create_space(db: Session, org_id: UUID, user_id: UUID, space_in: KnowledgeSpaceCreate) -> KnowledgeSpace:
    if space_in.project_id:
        # Check project
        proj = db.query(Project).filter(Project.id == space_in.project_id, Project.organization_id == org_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

    space = KnowledgeSpace(
        organization_id=org_id,
        project_id=space_in.project_id,
        name=space_in.name,
        slug=slugify(space_in.name),
        description=space_in.description,
        visibility=space_in.visibility,
        created_by=user_id
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="knowledge.space_created", entity_type="KNOWLEDGE", metadata={"space_id": str(space.id)})
    return space

def delete_space(db: Session, org_id: UUID, user_id: UUID, space_id: UUID):
    space = db.query(KnowledgeSpace).filter(KnowledgeSpace.id == space_id, KnowledgeSpace.organization_id == org_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    db.delete(space)
    db.commit()
    record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="knowledge.space_deleted", entity_type="KNOWLEDGE", metadata={"space_id": str(space_id)})

def get_documents(db: Session, org_id: UUID, space_id: Optional[UUID] = None) -> List[KnowledgeDocument]:
    query = db.query(KnowledgeDocument).filter(KnowledgeDocument.organization_id == org_id)
    if space_id:
        query = query.filter(KnowledgeDocument.space_id == space_id)
    return query.all()

def create_document(db: Session, org_id: UUID, user_id: UUID, doc_in: KnowledgeDocumentCreate) -> KnowledgeDocument:
    space = db.query(KnowledgeSpace).filter(KnowledgeSpace.id == doc_in.space_id, KnowledgeSpace.organization_id == org_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    if doc_in.parent_id:
        parent = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_in.parent_id, KnowledgeDocument.organization_id == org_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent document not found")

    doc = KnowledgeDocument(
        organization_id=org_id,
        space_id=doc_in.space_id,
        parent_id=doc_in.parent_id,
        title=doc_in.title,
        slug=slugify(doc_in.title),
        content=doc_in.content,
        content_format=doc_in.content_format,
        status=doc_in.status,
        is_pinned=doc_in.is_pinned,
        created_by=user_id,
        updated_by=user_id
    )
    db.add(doc)
    db.flush()

    # Create Initial Version
    ver = KnowledgeDocumentVersion(
        document_id=doc.id,
        version_number=1,
        title=doc.title,
        content=doc.content,
        change_summary="Initial commit",
        created_by=user_id
    )
    db.add(ver)

    if doc_in.tags:
        tags = db.query(KnowledgeTag).filter(KnowledgeTag.id.in_(doc_in.tags), KnowledgeTag.organization_id == org_id).all()
        doc.tags.extend(tags)

    db.commit()
    db.refresh(doc)
    record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="knowledge.document_created", entity_type="KNOWLEDGE", metadata={"document_id": str(doc.id)})
    return doc

def check_circular_dependency(db: Session, doc_id: UUID, new_parent_id: UUID) -> bool:
    curr = new_parent_id
    while curr:
        if curr == doc_id:
            return True
        parent = db.query(KnowledgeDocument.parent_id).filter(KnowledgeDocument.id == curr).first()
        if parent:
            curr = parent[0]
        else:
            curr = None
    return False

def update_document(db: Session, org_id: UUID, user_id: UUID, doc_id: UUID, doc_in: KnowledgeDocumentUpdate) -> KnowledgeDocument:
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id, KnowledgeDocument.organization_id == org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    content_changed = False
    old_title = doc.title
    old_content = doc.content

    if doc_in.title is not None and doc_in.title != doc.title:
        doc.title = doc_in.title
        doc.slug = slugify(doc_in.title)
        content_changed = True
    if doc_in.content is not None and doc_in.content != doc.content:
        doc.content = doc_in.content
        content_changed = True
    if doc_in.parent_id is not None and doc_in.parent_id != doc.parent_id:
        if check_circular_dependency(db, doc.id, doc_in.parent_id):
            raise HTTPException(status_code=400, detail="Circular dependency detected")
        doc.parent_id = doc_in.parent_id
    if doc_in.status is not None:
        doc.status = doc_in.status
    if doc_in.is_pinned is not None:
        doc.is_pinned = doc_in.is_pinned
        if doc_in.is_pinned:
            record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="knowledge.document_pinned", entity_type="KNOWLEDGE", metadata={"document_id": str(doc.id)})
    
    if doc_in.tags is not None:
        tags = db.query(KnowledgeTag).filter(KnowledgeTag.id.in_(doc_in.tags), KnowledgeTag.organization_id == org_id).all()
        doc.tags = tags

    doc.updated_by = user_id

    if content_changed:
        latest_ver = db.query(KnowledgeDocumentVersion).filter(KnowledgeDocumentVersion.document_id == doc.id).order_by(KnowledgeDocumentVersion.version_number.desc()).first()
        v_num = latest_ver.version_number + 1 if latest_ver else 1
        ver = KnowledgeDocumentVersion(
            document_id=doc.id,
            version_number=v_num,
            title=doc.title,
            content=doc.content,
            change_summary=doc_in.change_summary or "Updated document",
            created_by=user_id
        )
        db.add(ver)

    db.commit()
    db.refresh(doc)
    record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="knowledge.document_updated", entity_type="KNOWLEDGE", metadata={"document_id": str(doc.id)})
    return doc

def delete_document(db: Session, org_id: UUID, user_id: UUID, doc_id: UUID):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id, KnowledgeDocument.organization_id == org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="knowledge.document_deleted", entity_type="KNOWLEDGE", metadata={"document_id": str(doc_id)})

def restore_version(db: Session, org_id: UUID, user_id: UUID, doc_id: UUID, version_id: UUID) -> KnowledgeDocument:
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id, KnowledgeDocument.organization_id == org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    version = db.query(KnowledgeDocumentVersion).filter(KnowledgeDocumentVersion.id == version_id, KnowledgeDocumentVersion.document_id == doc_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    doc.title = version.title
    doc.slug = slugify(version.title)
    doc.content = version.content
    doc.updated_by = user_id
    
    latest_ver = db.query(KnowledgeDocumentVersion).filter(KnowledgeDocumentVersion.document_id == doc.id).order_by(KnowledgeDocumentVersion.version_number.desc()).first()
    v_num = latest_ver.version_number + 1
    new_ver = KnowledgeDocumentVersion(
        document_id=doc.id,
        version_number=v_num,
        title=doc.title,
        content=doc.content,
        change_summary=f"Restored from version {version.version_number}",
        created_by=user_id
    )
    db.add(new_ver)
    db.commit()
    db.refresh(doc)
    record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="knowledge.document_restored", entity_type="KNOWLEDGE", metadata={"document_id": str(doc.id), "version_number": v_num})
    return doc

def create_link(db: Session, org_id: UUID, user_id: UUID, doc_id: UUID, link_in: KnowledgeDocumentLinkCreate) -> KnowledgeDocumentLink:
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id, KnowledgeDocument.organization_id == org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    link = KnowledgeDocumentLink(
        document_id=doc.id,
        entity_type=link_in.entity_type,
        entity_id=link_in.entity_id
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="knowledge.document_linked", entity_type="KNOWLEDGE", metadata={"document_id": str(doc.id), "entity_type": str(link_in.entity_type)})
    return link
