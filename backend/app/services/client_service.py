from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.client import Client, ClientUser, ClientProjectAccess, ClientRequest, ClientComment, ClientActivity, ClientRequestStatus
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate, ClientRequestCreate, ClientRequestUpdate, ClientCommentCreate
from app.services.audit_service import record_event

def get_client(db: Session, client_id: UUID, org_id: UUID) -> Client:
    client = db.query(Client).filter(Client.id == client_id, Client.organization_id == org_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

def create_client(db: Session, org_id: UUID, user_id: UUID, client_in: ClientCreate) -> Client:
    client = Client(
        organization_id=org_id,
        name=client_in.name,
        email=client_in.email,
        company_name=client_in.company_name,
        phone=client_in.phone
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    record_event(db=db, organization_id=org_id, actor_user_id=user_id, event_type="CLIENT_CREATED", entity_type="CLIENT", entity_id=client.id)
    return client

def get_clients(db: Session, org_id: UUID) -> List[Client]:
    return db.query(Client).filter(Client.organization_id == org_id).all()

# Client portal logic (secure by user's client membership)
def get_user_clients(db: Session, user_id: UUID) -> List[Client]:
    return db.query(Client).join(ClientUser).filter(ClientUser.user_id == user_id).all()

def verify_client_access(db: Session, client_id: UUID, user_id: UUID) -> Client:
    cu = db.query(ClientUser).filter(ClientUser.client_id == client_id, ClientUser.user_id == user_id).first()
    if not cu:
        raise HTTPException(status_code=403, detail="Not a member of this client")
    client = db.query(Client).filter(Client.id == client_id).first()
    return client

def get_client_projects(db: Session, client_id: UUID) -> List[Project]:
    return db.query(Project).join(ClientProjectAccess, ClientProjectAccess.project_id == Project.id).filter(ClientProjectAccess.client_id == client_id).all()

def verify_client_project_access(db: Session, client_id: UUID, project_id: UUID):
    cpa = db.query(ClientProjectAccess).filter(ClientProjectAccess.client_id == client_id, ClientProjectAccess.project_id == project_id).first()
    if not cpa:
        raise HTTPException(status_code=403, detail="Client has no access to this project")

def create_client_request(db: Session, client_id: UUID, org_id: UUID, user_id: UUID, req_in: ClientRequestCreate) -> ClientRequest:
    if req_in.project_id:
        verify_client_project_access(db, client_id, req_in.project_id)
        
    req = ClientRequest(
        organization_id=org_id,
        client_id=client_id,
        project_id=req_in.project_id,
        title=req_in.title,
        description=req_in.description,
        priority=req_in.priority
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    
    # Record activity
    act = ClientActivity(organization_id=org_id, client_id=client_id, event_type="REQUEST_CREATED", entity_type="REQUEST", entity_id=req.id)
    db.add(act)
    db.commit()

    # Phase 36: notify the org (client request created)
    try:
        from app.services.notification_service import notify_client_request
        actor = db.query(User).filter(User.id == user_id).first()
        notify_client_request(
            db, org_id, req.id, req.title, "created",
            actor.name if actor else "A client",
        )
    except Exception:
        pass
    return req
