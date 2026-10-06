from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID
import re

from app.api import deps
from app.models.user import User
from app.models.task import TaskTemplate, Task, Label, ChecklistItem, TaskPriority, TaskLabel
from app.models.project import Project
from app.models.project_template import ProjectTemplate, ProjectTemplateTask
from app.schemas.template import (
    TaskTemplateCreate, TaskTemplateUpdate, TaskTemplateResponse,
    ProjectTemplateCreate, ProjectTemplateUpdate, ProjectTemplateResponse,
    ProjectFromTemplateCreate, ProjectFromTemplateResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Existing task-level templates (unchanged behavior)
# ---------------------------------------------------------------------------

@router.post("/task", response_model=TaskTemplateResponse, status_code=status.HTTP_201_CREATED)
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

@router.get("/task", response_model=List[TaskTemplateResponse])
def list_templates(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    return db.query(TaskTemplate).filter(TaskTemplate.organization_id == org_id).all()

@router.patch("/task/{template_id}", response_model=TaskTemplateResponse)
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

@router.delete("/task/{template_id}")
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


# ---------------------------------------------------------------------------
# Phase 44 — Project templates (organization-scoped CRUD)
# ---------------------------------------------------------------------------

def _get_project_template_or_404(db: Session, org_id: UUID, template_id: UUID) -> ProjectTemplate:
    template = db.query(ProjectTemplate).filter(
        ProjectTemplate.id == template_id,
        ProjectTemplate.organization_id == org_id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/project", response_model=ProjectTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_project_template(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    template_in: ProjectTemplateCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    if not template_in.name.strip():
        raise HTTPException(status_code=422, detail="Template name cannot be empty")

    template = ProjectTemplate(
        name=template_in.name.strip(),
        description=template_in.description,
        organization_id=org_id,
        created_by_id=current_user.id,
    )
    for i, t in enumerate(template_in.tasks):
        db.add(ProjectTemplateTask(
            template=template,
            title=t.title.strip(),
            description=t.description,
            priority=t.priority,
            position=t.position if t.position else i,
            label_names=list(dict.fromkeys(t.label_names)),
            checklist_items=list(dict.fromkeys(t.checklist_items)),
        ))
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/project", response_model=List[ProjectTemplateResponse])
def list_project_templates(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    current_user: User = Depends(deps.get_current_user),
    include_archived: bool = False,
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    q = db.query(ProjectTemplate).filter(ProjectTemplate.organization_id == org_id)
    if not include_archived:
        q = q.filter(ProjectTemplate.is_archived == False)  # noqa: E712
    return q.order_by(ProjectTemplate.created_at.desc()).all()


@router.get("/project/{template_id}", response_model=ProjectTemplateResponse)
def get_project_template(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    template_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    return _get_project_template_or_404(db, org_id, template_id)


@router.patch("/project/{template_id}", response_model=ProjectTemplateResponse)
def update_project_template(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    template_id: UUID,
    template_in: ProjectTemplateUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    template = _get_project_template_or_404(db, org_id, template_id)

    data = template_in.model_dump(exclude_unset=True)
    if "name" in data and not (data["name"] or "").strip():
        raise HTTPException(status_code=422, detail="Template name cannot be empty")

    # Replace full task list when provided; keeps ordering simple and avoids
    # orphaned task definitions.
    tasks_in = data.pop("tasks", None)
    for field, value in data.items():
        setattr(template, field, value)
    if tasks_in is not None:
        template.tasks.clear()
        db.flush()
        for i, t in enumerate(tasks_in):
            db.add(ProjectTemplateTask(
                template=template,
                title=t["title"].strip(),
                description=t.get("description"),
                priority=t.get("priority") or TaskPriority.MEDIUM,
                position=t.get("position") if t.get("position") else i,
                label_names=list(dict.fromkeys(t.get("label_names") or [])),
                checklist_items=list(dict.fromkeys(t.get("checklist_items") or [])),
            ))
    db.commit()
    db.refresh(template)
    return template


@router.delete("/project/{template_id}")
def delete_project_template(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    template_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    template = _get_project_template_or_404(db, org_id, template_id)
    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}


@router.post("/project/{template_id}/archive", response_model=ProjectTemplateResponse)
def archive_project_template(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    template_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    template = _get_project_template_or_404(db, org_id, template_id)
    template.is_archived = True
    db.commit()
    db.refresh(template)
    return template


# ---------------------------------------------------------------------------
# Phase 44 — Create project from template
# ---------------------------------------------------------------------------

@router.post("/project/{template_id}/create-project", response_model=ProjectFromTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_project_from_template(
    *,
    db: Session = Depends(deps.get_db),
    org_id: UUID = Depends(deps.get_current_organization_id),
    template_id: UUID,
    project_in: ProjectFromTemplateCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    # Creating a project is an owner/admin-level action (matches projects API).
    from app.models.organization import OrganizationRole
    if member.role not in (OrganizationRole.OWNER, OrganizationRole.ADMIN):
        raise HTTPException(status_code=403, detail="You do not have permission to create projects in this organization")

    template = _get_project_template_or_404(db, org_id, template_id)
    if template.is_archived:
        raise HTTPException(status_code=400, detail="Cannot create a project from an archived template")

    if not project_in.name.strip():
        raise HTTPException(status_code=422, detail="Project name cannot be empty")

    # Resolve labels by name within this organization (template only stores names).
    template_tasks = sorted(template.tasks, key=lambda t: t.position)
    all_label_names = {n for t in template_tasks for n in (t.label_names or [])}
    labels_by_name = {}
    if all_label_names:
        found = db.query(Label).filter(Label.organization_id == org_id, Label.name.in_(all_label_names)).all()
        labels_by_name = {l.name: l for l in found}

    try:
        base_slug = re.sub(r'[^a-z0-9]+', '-', project_in.name.lower()).strip('-') or "project"
        slug = base_slug
        counter = 1
        while db.query(Project).filter(Project.organization_id == org_id, Project.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        project = Project(
            name=project_in.name.strip(),
            description=project_in.description,
            owner_id=current_user.id,
            organization_id=org_id,
            slug=slug,
            key=(re.sub(r'[^A-Za-z0-9]', '', project_in.name)[:5].upper() or "PROJ"),
        )
        db.add(project)
        db.flush()  # assign project.id without committing yet

        # Pre-compute globally-unique task_keys in bulk (task_key has a global
        # UNIQUE index; two projects may otherwise derive the same key).
        seq = 0
        candidate_keys = []
        for tt in template_tasks:
            seq += 1
            candidate_keys.append(f"{project.key}-{seq}" if project.key else f"PROJ-{seq}")
        taken = {k for (k,) in db.query(Task.task_key).filter(Task.task_key.in_(candidate_keys)).all()} if candidate_keys else set()

        seq = 0
        for tt in template_tasks:
            seq += 1
            project.task_seq_num = seq
            base_key = candidate_keys[seq - 1]
            task_key = base_key
            suffix = 0
            while task_key in taken:
                suffix += 1
                task_key = f"{base_key}-{suffix}"
            taken.add(task_key)
            task = Task(
                project_id=project.id,
                creator_id=current_user.id,
                title=tt.title,
                description=tt.description,
                priority=tt.priority,
                position=tt.position,
                task_key=task_key,
            )
            db.add(task)
            db.flush()
            for name in (tt.label_names or []):
                label = labels_by_name.get(name)
                if label is not None:
                    db.add(TaskLabel(task_id=task.id, label_id=label.id))
            for pos, text in enumerate(tt.checklist_items or []):
                db.add(ChecklistItem(task_id=task.id, text=text, position=float(pos)))

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(project)
    return ProjectFromTemplateResponse(
        project_id=project.id,
        name=project.name,
        slug=project.slug,
        tasks_created=seq,
    )
