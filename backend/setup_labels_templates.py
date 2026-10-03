import os

template_schema = """from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.task import TaskPriority

class TaskTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    title_template: Optional[str] = None
    description_template: Optional[str] = None
    priority_template: Optional[TaskPriority] = None
    labels_template: List[str] = []
    checklist_template: List[str] = []

class TaskTemplateCreate(TaskTemplateBase):
    pass

class TaskTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    title_template: Optional[str] = None
    description_template: Optional[str] = None
    priority_template: Optional[TaskPriority] = None
    labels_template: Optional[List[str]] = None
    checklist_template: Optional[List[str]] = None

class TaskTemplateResponse(TaskTemplateBase):
    id: UUID
    organization_id: UUID
    created_by_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
"""

with open("c:/personal_projects/devflow/backend/app/schemas/template.py", "w", encoding="utf-8") as f:
    f.write(template_schema)

labels_api = """from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.task import Label
from app.schemas.label import LabelCreate, LabelUpdate, LabelResponse

router = APIRouter()

@router.post("", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
def create_label(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    label_in: LabelCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    # Could restrict to admin/owner here
    existing = db.query(Label).filter(Label.organization_id == org_id, Label.name == label_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Label already exists in this organization")
        
    label = Label(**label_in.model_dump(), organization_id=org_id)
    db.add(label)
    db.commit()
    db.refresh(label)
    return label

@router.get("", response_model=List[LabelResponse])
def list_labels(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    return db.query(Label).filter(Label.organization_id == org_id).all()

@router.patch("/{label_id}", response_model=LabelResponse)
def update_label(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    label_id: UUID,
    label_in: LabelUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    label = db.query(Label).filter(Label.id == label_id, Label.organization_id == org_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
        
    update_data = label_in.model_dump(exclude_unset=True)
    if 'name' in update_data and update_data['name'] != label.name:
        existing = db.query(Label).filter(Label.organization_id == org_id, Label.name == update_data['name']).first()
        if existing:
            raise HTTPException(status_code=400, detail="Label name already in use")
            
    for field, value in update_data.items():
        setattr(label, field, value)
    db.commit()
    db.refresh(label)
    return label

@router.delete("/{label_id}")
def delete_label(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    label_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    label = db.query(Label).filter(Label.id == label_id, Label.organization_id == org_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    db.delete(label)
    db.commit()
    return {"message": "Label deleted"}
"""

templates_api = """from fastapi import APIRouter, Depends, HTTPException, status
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
"""

with open("c:/personal_projects/devflow/backend/app/api/v1/labels.py", "w", encoding="utf-8") as f:
    f.write(labels_api)

with open("c:/personal_projects/devflow/backend/app/api/v1/templates.py", "w", encoding="utf-8") as f:
    f.write(templates_api)

main_path = "c:/personal_projects/devflow/backend/app/main.py"
with open(main_path, "r", encoding="utf-8") as f:
    main_content = f.read()

main_content = main_content.replace(
    "from app.api.v1 import auth, projects, tasks, dashboard, github, ai, analytics, notifications, organizations, teams, invitations",
    "from app.api.v1 import auth, projects, tasks, dashboard, github, ai, analytics, notifications, organizations, teams, invitations, labels, templates"
)
main_content = main_content.replace(
    'app.include_router(invitations.router, prefix=f"{settings.API_V1_STR}/invitations", tags=["invitations"])',
    'app.include_router(invitations.router, prefix=f"{settings.API_V1_STR}/invitations", tags=["invitations"])\napp.include_router(labels.router, prefix=f"{settings.API_V1_STR}/labels", tags=["labels"])\napp.include_router(templates.router, prefix=f"{settings.API_V1_STR}/templates", tags=["templates"])'
)
with open(main_path, "w", encoding="utf-8") as f:
    f.write(main_content)
print("Labels and templates API created and linked")
