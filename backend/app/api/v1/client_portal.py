from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from app.api.deps import get_db, get_current_user, get_current_organization_id
from app.models.user import User
from app.models.organization import Organization
from app.models.task import Task
from app.schemas.client import ClientResponse, ClientRequestResponse, ClientRequestCreate
from app.services import client_service

router = APIRouter()

@router.get("/me", response_model=List[ClientResponse])
def get_my_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # A user can be part of multiple clients
    return client_service.get_user_clients(db, current_user.id)

@router.get("/{client_id}/projects")
def get_projects(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client_service.verify_client_access(db, client_id, current_user.id)
    projects = client_service.get_client_projects(db, client_id)
    return [{"id": p.id, "name": p.name, "description": p.description} for p in projects]

@router.get("/{client_id}/projects/{project_id}/tasks")
def get_project_tasks(
    client_id: UUID,
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client_service.verify_client_access(db, client_id, current_user.id)
    client_service.verify_client_project_access(db, client_id, project_id)
    
    tasks = db.query(Task).filter(Task.project_id == project_id, Task.client_visible == True).all()
    return [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority} for t in tasks]

@router.post("/{client_id}/requests", response_model=ClientRequestResponse)
def create_request(
    client_id: UUID,
    req_in: ClientRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id) # Ensure we still enforce org context
):
    client = client_service.verify_client_access(db, client_id, current_user.id)
    if client.organization_id != org_id:
        raise HTTPException(status_code=403, detail="Client does not belong to this organization")
        
    return client_service.create_client_request(db, client_id, org_id, current_user.id, req_in)

@router.get("/{client_id}/requests", response_model=List[ClientRequestResponse])
def get_requests(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = client_service.verify_client_access(db, client_id, current_user.id)
    from app.models.client import ClientRequest
    return db.query(ClientRequest).filter(ClientRequest.client_id == client_id).all()
