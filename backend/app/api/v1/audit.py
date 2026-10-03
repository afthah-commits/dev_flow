from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

from app.api import deps
from app.models.user import User
from app.models.audit import AuditEvent
from app.models.organization import OrganizationRole
from pydantic import BaseModel

router = APIRouter()

class AuditEventResponse(BaseModel):
    id: UUID
    organization_id: Optional[UUID]
    actor_user_id: Optional[UUID]
    event_type: str
    entity_type: str
    entity_id: Optional[UUID]
    project_id: Optional[UUID]
    team_id: Optional[UUID]
    metadata_: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/events", response_model=dict)
def list_events(
    organization_id: UUID,
    project_id: Optional[UUID] = None,
    team_id: Optional[UUID] = None,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    # Verify org member
    deps.require_organization_member(db, current_user.id, organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    query = db.query(AuditEvent).filter(AuditEvent.organization_id == organization_id)
    if project_id:
        query = query.filter(AuditEvent.project_id == project_id)
    if team_id:
        query = query.filter(AuditEvent.team_id == team_id)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
        
    total = query.count()
    events = query.order_by(desc(AuditEvent.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    # We map metadata_ to metadata in response manually if needed, or rely on Config alias
    resp_events = []
    for e in events:
        resp_events.append({
            "id": e.id,
            "organization_id": e.organization_id,
            "actor_user_id": e.actor_user_id,
            "event_type": e.event_type,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "project_id": e.project_id,
            "team_id": e.team_id,
            "metadata": e.metadata_,
            "created_at": e.created_at
        })
        
    return {
        "items": resp_events,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/events/export")
def export_events(
    organization_id: UUID,
    project_id: Optional[UUID] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    deps.require_organization_member(db, current_user.id, organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    query = db.query(AuditEvent).filter(AuditEvent.organization_id == organization_id)
    if project_id:
        query = query.filter(AuditEvent.project_id == project_id)
        
    events = query.order_by(desc(AuditEvent.created_at)).limit(5000).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Actor", "Event Type", "Entity Type", "Entity ID", "Project ID"])
    
    for e in events:
        writer.writerow([
            str(e.id),
            e.created_at.isoformat() if e.created_at else "",
            str(e.actor_user_id),
            e.event_type,
            e.entity_type,
            str(e.entity_id),
            str(e.project_id)
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_export_{organization_id}.csv"}
    )
