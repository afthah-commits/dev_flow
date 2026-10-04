from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from app.api.deps import get_db, get_current_user, get_current_organization_id, require_organization_member
from app.models.user import User
from app.models.organization import OrganizationRole
from app.models.workflow import Workflow, WorkflowState, WorkflowTransition, WorkflowExecution, WorkflowExecutionEvent
from app.schemas.workflow import WorkflowResponse, WorkflowCreate, WorkflowUpdate

router = APIRouter()

@router.get("", response_model=List[WorkflowResponse])
def get_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    require_organization_member(db, current_user.id, org_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER])
    return db.query(Workflow).filter(Workflow.organization_id == org_id).all()

@router.post("", response_model=WorkflowResponse)
def create_workflow(
    workflow_in: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    require_organization_member(db, current_user.id, org_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    workflow = Workflow(
        organization_id=org_id,
        name=workflow_in.name,
        description=workflow_in.description,
        entity_type=workflow_in.entity_type,
        is_active=workflow_in.is_active,
        created_by=current_user.id
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    for s in workflow_in.states:
        state = WorkflowState(workflow_id=workflow.id, **s.model_dump())
        db.add(state)
        
    for t in workflow_in.transitions:
        trans = WorkflowTransition(workflow_id=workflow.id, **t.model_dump())
        db.add(trans)
        
    db.commit()
    db.refresh(workflow)
    return workflow

@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    require_organization_member(db, current_user.id, org_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER])
    wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.organization_id == org_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf

@router.post("/{workflow_id}/transitions/{transition_id}/execute")
def execute_transition(
    workflow_id: UUID,
    transition_id: UUID,
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(get_current_organization_id)
):
    require_organization_member(db, current_user.id, org_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MEMBER])
    wf = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.organization_id == org_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    trans = db.query(WorkflowTransition).filter(WorkflowTransition.id == transition_id, WorkflowTransition.workflow_id == workflow_id).first()
    if not trans:
        raise HTTPException(status_code=404, detail="Transition not found")
        
    # In a full implementation, we would evaluate conditions and execute actions here securely without eval()
    # using safe field comparators.
    
    return {"status": "success", "message": "Transition executed"}
