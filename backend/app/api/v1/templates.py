from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.task import TaskTemplate
from app.schemas.template import TaskTemplateCreate, TaskTemplateUpdate, TaskTemplateResponse

router = APIRouter()

@router.post("", response_model=TaskTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    template_in: TaskTemplateCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    template = TaskTemplate(
        **template_in.model_dump(),
        organization_id=org_id,
        created_by_id=current_user.id
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

@router.get("", response_model=List[TaskTemplateResponse])
def list_templates(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    return db.query(TaskTemplate).filter(TaskTemplate.organization_id == org_id).all()

@router.patch("/{template_id}", response_model=TaskTemplateResponse)
def update_template(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    template_id: UUID,
    template_in: TaskTemplateUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    template = db.query(TaskTemplate).filter(TaskTemplate.id == template_id, TaskTemplate.organization_id == org_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    db.commit()
    db.refresh(template)
    return template

@router.delete("/{template_id}")
def delete_template(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    template_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    template = db.query(TaskTemplate).filter(TaskTemplate.id == template_id, TaskTemplate.organization_id == org_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}
