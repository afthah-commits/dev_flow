from fastapi import APIRouter, Depends, Query
from typing import Any, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.collaboration import Discussion
from app.models.knowledge import KnowledgeDocument

router = APIRouter()

@router.get("")
def search_global(
    q: str = Query(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    
    term = f"%{q}%"
    results = []

    # Knowledge Documents
    docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.organization_id == org_id,
        or_(
            KnowledgeDocument.title.ilike(term),
            KnowledgeDocument.content.ilike(term)
        )
    ).limit(10).all()
    for d in docs:
        results.append({
            "entity_type": "DOCUMENT",
            "entity_id": str(d.id),
            "title": d.title,
            "description": d.content[:100] if d.content else "",
            "matched_field": "title/content",
            "url": f"/knowledge/documents/{d.id}",
            "score": 1.0
        })

    # Projects
    projects = db.query(Project).filter(Project.organization_id == org_id, Project.name.ilike(term)).limit(5).all()
    for p in projects:
        results.append({
            "entity_type": "PROJECT",
            "entity_id": str(p.id),
            "title": p.name,
            "description": p.description or "",
            "matched_field": "name",
            "url": f"/projects/{p.id}",
            "score": 0.8
        })

    # Tasks
    tasks = db.query(Task).join(Project).filter(Project.organization_id == org_id, Task.title.ilike(term)).limit(5).all()
    for t in tasks:
        results.append({
            "entity_type": "TASK",
            "entity_id": str(t.id),
            "title": t.title,
            "description": t.description or "",
            "matched_field": "title",
            "url": f"/projects/{t.project_id}/tasks/{t.id}",
            "score": 0.9
        })

    # Discussions
    discussions = db.query(Discussion).filter(Discussion.organization_id == org_id, Discussion.title.ilike(term)).limit(5).all()
    for d in discussions:
        results.append({
            "entity_type": "DISCUSSION",
            "entity_id": str(d.id),
            "title": d.title,
            "description": d.content[:100] if d.content else "",
            "matched_field": "title",
            "url": f"/projects/{d.project_id}/discussions/{d.id}",
            "score": 0.7
        })

    return results
