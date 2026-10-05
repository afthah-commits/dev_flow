import random
from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from app.api import deps
from app.models.user import User
from app.services.release_engine import ReleaseEngine
from app.services.audit_service import record_event
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.delivery import (
    Release, ReleaseStatus, ReleaseType, ReleaseTask, ReleasePullRequest,
    Environment, Deployment, DeploymentStatus, DeploymentProvider,
    PipelineRun, PipelineStatus, ReleaseApproval, ReleaseApprovalStatus
)
from app.schemas.delivery import (
    ReleaseCreate, ReleaseUpdate, ReleaseResponse, ReleaseReadiness,
    EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse,
    DeploymentCreate, DeploymentResponse,
    PipelineRunCreate, PipelineRunResponse,
    DeliveryMetrics, DoraMetrics, ReleaseApprovalCreate, ReleaseApprovalResponse
)

project_releases_router = APIRouter()
releases_router = APIRouter()
environments_router = APIRouter()
project_deployments_router = APIRouter()
deployments_router = APIRouter()
pipelines_router = APIRouter()

# --- RELEASES (Project Level) ---
@project_releases_router.post("", response_model=ReleaseResponse, status_code=status.HTTP_201_CREATED)
def create_release(
    project_id: UUID,
    release_in: ReleaseCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    project = db.query(Project).filter(Project.id == project_id, Project.organization_id == org_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = db.query(Release).filter(Release.project_id == project_id, Release.version == release_in.version).first()
    if existing:
        raise HTTPException(status_code=400, detail="Version already exists in this project")

    release = Release(
        organization_id=org_id,
        project_id=project_id,
        name=release_in.name,
        version=release_in.version,
        description=release_in.description,
        release_type=release_in.release_type,
        target_environment=release_in.target_environment,
        git_tag=release_in.git_tag,
        target_commit_sha=release_in.target_commit_sha,
        planned_at=release_in.planned_at,
        created_by_id=current_user.id
    )
    db.add(release)
    db.commit()
    db.refresh(release)
    return release

@project_releases_router.get("", response_model=List[ReleaseResponse])
def list_releases(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    return db.query(Release).filter(Release.project_id == project_id).order_by(Release.created_at.desc()).all()

@project_releases_router.get("/{release_id}", response_model=ReleaseResponse)
def get_release(
    project_id: UUID,
    release_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.project_id == project_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    return release

@project_releases_router.patch("/{release_id}", response_model=ReleaseResponse)
def update_release(
    project_id: UUID,
    release_id: UUID,
    release_in: ReleaseUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.project_id == project_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    
    update_data = release_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(release, field, value)
    
    db.commit()
    db.refresh(release)
    return release

@project_releases_router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_release(
    project_id: UUID,
    release_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.project_id == project_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    db.delete(release)
    db.commit()
    return None

# --- RELEASES LIFECYCLE (Top Level) ---
@releases_router.post("/{release_id}/plan", response_model=ReleaseResponse)
def plan_release(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    if release.status != ReleaseStatus.DRAFT: raise HTTPException(status_code=400, detail="Only DRAFT releases can be planned")
    release.status = ReleaseStatus.READY
    db.commit()
    db.refresh(release)
    return release

@releases_router.post("/{release_id}/ready", response_model=ReleaseResponse)
def ready_release(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    if release.status != ReleaseStatus.READY: raise HTTPException(status_code=400, detail="Only PLANNED releases can be marked ready")
    release.status = ReleaseStatus.READY
    db.commit()
    db.refresh(release)
    return release

@releases_router.post("/{release_id}/release", response_model=ReleaseResponse)
def execute_release(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    if release.status not in [ReleaseStatus.READY, ReleaseStatus.READY]: raise HTTPException(status_code=400, detail="Release must be READY or PLANNED to release")
    release.status = ReleaseStatus.DEPLOYED
    release.released_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(release)
    return release

@releases_router.post("/{release_id}/cancel", response_model=ReleaseResponse)
def cancel_release(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    release.status = ReleaseStatus.CANCELLED
    db.commit()
    db.refresh(release)
    return release

# --- ENVIRONMENTS (Project Level) ---
@environments_router.post("", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED)
def create_env(project_id: UUID, env_in: EnvironmentCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    if db.query(Environment).filter(Environment.project_id == project_id, Environment.name == env_in.name).first():
        raise HTTPException(status_code=400, detail="Environment name already exists")
    env = Environment(organization_id=org_id, project_id=project_id, **env_in.model_dump())
    db.add(env)
    db.commit()
    db.refresh(env)
    return env

@environments_router.get("", response_model=List[EnvironmentResponse])
def list_envs(project_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    return db.query(Environment).filter(Environment.project_id == project_id).all()

@environments_router.patch("/{env_id}", response_model=EnvironmentResponse)
def update_env(project_id: UUID, env_id: UUID, env_in: EnvironmentUpdate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    env = db.query(Environment).filter(Environment.id == env_id, Environment.project_id == project_id).first()
    if not env: raise HTTPException(status_code=404, detail="Environment not found")
    for k, v in env_in.model_dump(exclude_unset=True).items():
        setattr(env, k, v)
    db.commit()
    db.refresh(env)
    return env

@environments_router.delete("/{env_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_env(project_id: UUID, env_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    env = db.query(Environment).filter(Environment.id == env_id, Environment.project_id == project_id).first()
    if not env: raise HTTPException(status_code=404, detail="Environment not found")
    db.delete(env)
    db.commit()
    return None

# --- DEPLOYMENTS (Release/Project/Top level) ---
@releases_router.post("/{release_id}/deploy", response_model=DeploymentResponse)
def deploy_release(release_id: UUID, dep_in: DeploymentCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    
    # Mock deployment behavior
    dep_status = DeploymentStatus.SUCCESS
    duration = random.randint(10, 120)
    
    dep = Deployment(
        organization_id=org_id,
        project_id=release.project_id,
        release_id=release.id,
        environment_id=dep_in.environment_id,
        status=dep_status,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=duration,
        triggered_by_id=current_user.id,
        provider=dep_in.provider,
        commit_sha=release.target_commit_sha
    )
    db.add(dep)
    
    release.status = ReleaseStatus.DEPLOYED
    release.deployment_timestamp = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(dep)
    return dep

@project_deployments_router.get("", response_model=List[DeploymentResponse])
def list_deployments(project_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    return db.query(Deployment).filter(Deployment.project_id == project_id).order_by(Deployment.created_at.desc()).all()

@deployments_router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(deployment_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    dep = db.query(Deployment).filter(Deployment.id == deployment_id, Deployment.organization_id == org_id).first()
    if not dep: raise HTTPException(status_code=404, detail="Deployment not found")
    return dep

@deployments_router.post("/{deployment_id}/rollback", response_model=DeploymentResponse)
def rollback_deployment(deployment_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    dep = db.query(Deployment).filter(Deployment.id == deployment_id, Deployment.organization_id == org_id).first()
    if not dep: raise HTTPException(status_code=404, detail="Deployment not found")
    
    dep.status = DeploymentStatus.ROLLED_BACK
    
    rb_dep = Deployment(
        organization_id=org_id,
        project_id=dep.project_id,
        release_id=dep.release_id,
        environment_id=dep.environment_id,
        status=DeploymentStatus.SUCCESS,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=5,
        triggered_by_id=current_user.id,
        provider=dep.provider,
        previous_deployment_id=dep.id
    )
    db.add(rb_dep)
    db.commit()
    db.refresh(rb_dep)
    return rb_dep

# --- PIPELINES ---
@pipelines_router.post("/run", response_model=PipelineRunResponse)
def run_pipeline(project_id: UUID, pipe_in: PipelineRunCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    pipe = PipelineRun(
        organization_id=org_id,
        project_id=project_id,
        provider=pipe_in.provider,
        branch=pipe_in.branch,
        commit_sha=pipe_in.commit_sha,
        workflow_name=pipe_in.workflow_name,
        status=PipelineStatus.SUCCESS,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=random.randint(20, 300)
    )
    db.add(pipe)
    db.commit()
    db.refresh(pipe)
    return pipe

@pipelines_router.get("", response_model=List[PipelineRunResponse])
def list_pipelines(project_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    return db.query(PipelineRun).filter(PipelineRun.project_id == project_id).order_by(PipelineRun.created_at.desc()).all()

# --- RELEASE ITEMS (Tasks/PRs) ---
@releases_router.post("/{release_id}/tasks/{task_id}")
def add_release_task(release_id: UUID, task_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    if task.project_id != release.project_id:
        raise HTTPException(status_code=400, detail="Task must belong to the same project as the release")
    existing = db.query(ReleaseTask).filter(ReleaseTask.release_id == release_id, ReleaseTask.task_id == task_id).first()
    if existing: raise HTTPException(status_code=400, detail="Task already in release")
    rt = ReleaseTask(release_id=release_id, task_id=task_id)
    db.add(rt)
    db.commit()
    return {"status": "ok"}

@releases_router.delete("/{release_id}/tasks/{task_id}")
def remove_release_task(release_id: UUID, task_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    rt = db.query(ReleaseTask).filter(ReleaseTask.release_id == release_id, ReleaseTask.task_id == task_id).first()
    if not rt: raise HTTPException(status_code=404, detail="Task not in release")
    db.delete(rt)
    db.commit()
    return {"status": "ok"}

@releases_router.get("/{release_id}/tasks")
def list_release_tasks(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    rts = db.query(ReleaseTask).filter(ReleaseTask.release_id == release_id).all()
    task_ids = [rt.task_id for rt in rts]
    if not task_ids:
        return []
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
    return [{"id": str(t.id), "title": t.title, "status": t.status.value if t.status else None, "priority": t.priority.value if t.priority else None} for t in tasks]

@releases_router.post("/{release_id}/prs")
def add_release_pr(release_id: UUID, data: dict, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    pr_number = data.get("pr_number")
    if not pr_number: raise HTTPException(status_code=400, detail="pr_number is required")
    existing = db.query(ReleasePullRequest).filter(ReleasePullRequest.release_id == release_id, ReleasePullRequest.pr_number == pr_number).first()
    if existing: raise HTTPException(status_code=400, detail="PR already in release")
    pr = ReleasePullRequest(release_id=release_id, pr_number=pr_number, pr_title=data.get("pr_title"), pr_url=data.get("pr_url"))
    db.add(pr)
    db.commit()
    return {"status": "ok", "id": str(pr.id)}

@releases_router.get("/{release_id}/prs")
def list_release_prs(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    prs = db.query(ReleasePullRequest).filter(ReleasePullRequest.release_id == release_id).all()
    return [{"id": str(p.id), "pr_number": p.pr_number, "pr_title": p.pr_title, "pr_url": p.pr_url} for p in prs]

@releases_router.delete("/{release_id}/prs/{pr_id}")
def remove_release_pr(release_id: UUID, pr_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    pr = db.query(ReleasePullRequest).filter(ReleasePullRequest.id == pr_id, ReleasePullRequest.release_id == release_id).first()
    if not pr: raise HTTPException(status_code=404, detail="PR not in release")
    db.delete(pr)
    db.commit()
    return {"status": "ok"}

# --- RELEASE NOTES ---
@releases_router.get("/{release_id}/notes")
def get_release_notes(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    return {"release_id": str(release.id), "version": release.version, "notes": release.description or ""}

@releases_router.patch("/{release_id}/notes")
def update_release_notes(release_id: UUID, data: dict, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    release.description = data.get("notes", release.description)
    db.commit()
    return {"status": "ok"}

# --- READINESS SCORE ---
@releases_router.get("/{release_id}/readiness", response_model=ReleaseReadiness)
def get_readiness(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    
    result = ReleaseEngine.evaluate_readiness(db, release)
    return ReleaseReadiness(**result)

# --- DELIVERY METRICS ---
delivery_metrics_router = APIRouter()

@delivery_metrics_router.get("/delivery")
def get_delivery_metrics(project_id: Optional[UUID] = None, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)

    dep_q = db.query(Deployment).filter(Deployment.organization_id == org_id)
    rel_q = db.query(Release).filter(Release.organization_id == org_id)
    pipe_q = db.query(PipelineRun).filter(PipelineRun.organization_id == org_id)
    if project_id:
        dep_q = dep_q.filter(Deployment.project_id == project_id)
        rel_q = rel_q.filter(Release.project_id == project_id)
        pipe_q = pipe_q.filter(PipelineRun.project_id == project_id)

    all_deps = dep_q.all()
    all_releases = rel_q.all()
    all_pipes = pipe_q.all()

    total_deps = len(all_deps)
    success_deps = sum(1 for d in all_deps if d.status == DeploymentStatus.SUCCESS)
    failed_deps = sum(1 for d in all_deps if d.status == DeploymentStatus.FAILED)
    rollback_deps = sum(1 for d in all_deps if d.status == DeploymentStatus.ROLLED_BACK)
    avg_dur = (sum(d.duration_seconds or 0 for d in all_deps) / total_deps) if total_deps else 0

    total_releases = len(all_releases)
    released = [r for r in all_releases if r.status == ReleaseStatus.DEPLOYED and r.released_at and r.created_at]
    avg_cycle = 0.0
    if released:
        cycles = [(r.released_at - r.created_at).total_seconds() / 86400 for r in released]
        avg_cycle = sum(cycles) / len(cycles)

    total_pipes = len(all_pipes)
    success_pipes = sum(1 for p in all_pipes if p.status == PipelineStatus.SUCCESS)
    pipe_rate = (success_pipes / total_pipes * 100) if total_pipes else 0

    # Lead time: average time from first task completion to release
    # Phase 31: batched into 2 queries instead of 2 queries per release (N+1).
    lead_times = []
    if released:
        released_ids = [r.id for r in released]
        release_tasks = db.query(ReleaseTask.release_id, ReleaseTask.task_id)\
            .filter(ReleaseTask.release_id.in_(released_ids)).all()
        all_task_ids = {rt.task_id for rt in release_tasks}
        done_tasks = {}
        if all_task_ids:
            done_tasks = {
                t.id: t for t in db.query(Task)
                .filter(Task.id.in_(all_task_ids), Task.status == TaskStatus.DONE).all()
            }
        tasks_by_release: dict = {}
        for rt in release_tasks:
            task = done_tasks.get(rt.task_id)
            if task is not None:
                tasks_by_release.setdefault(rt.release_id, []).append(task)

        for r in released:
            tasks = tasks_by_release.get(r.id, [])
            if tasks and r.released_at:
                earliest = min(t.updated_at or t.created_at for t in tasks)
                if earliest:
                    lead_times.append((r.released_at - earliest).total_seconds() / 86400)

    avg_lead = sum(lead_times) / len(lead_times) if lead_times else 0

    return {
        "deployment_frequency": total_deps,
        "successful_deployment_rate": (success_deps / total_deps * 100) if total_deps else 0,
        "failed_deployment_rate": (failed_deps / total_deps * 100) if total_deps else 0,
        "avg_deployment_duration_seconds": avg_dur,
        "release_frequency": total_releases,
        "avg_release_cycle_time_days": avg_cycle,
        "pipeline_success_rate": pipe_rate,
        "rollback_frequency": rollback_deps,
        "avg_lead_time_days": avg_lead
    }

@delivery_metrics_router.get("/dora")
def get_dora_metrics(project_id: Optional[UUID] = None, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)

    dep_q = db.query(Deployment).filter(Deployment.organization_id == org_id)
    if project_id:
        dep_q = dep_q.filter(Deployment.project_id == project_id)
    all_deps = dep_q.all()

    if len(all_deps) < 2:
        return {"deployment_frequency": "insufficient_data", "lead_time_for_changes": "insufficient_data", "change_failure_rate": "insufficient_data", "mean_time_to_recovery": "insufficient_data"}

    total = len(all_deps)
    failed = sum(1 for d in all_deps if d.status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK])
    cfr = f"{(failed / total * 100):.1f}%"

    sorted_deps = sorted(all_deps, key=lambda d: d.created_at)
    first = sorted_deps[0].created_at
    last = sorted_deps[-1].created_at
    span_days = max((last - first).days, 1)
    df = f"{total / span_days:.2f} per day" if span_days > 0 else "insufficient_data"

    # MTTR: avg time between FAILED and next SUCCESS
    mttr_times = []
    for i, d in enumerate(sorted_deps):
        if d.status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]:
            for j in range(i + 1, len(sorted_deps)):
                if sorted_deps[j].status == DeploymentStatus.SUCCESS:
                    mttr_times.append((sorted_deps[j].completed_at - d.completed_at).total_seconds() / 3600 if sorted_deps[j].completed_at and d.completed_at else 0)
                    break

    mttr = f"{sum(mttr_times) / len(mttr_times):.1f} hours" if mttr_times else "insufficient_data"

    return {"deployment_frequency": df, "lead_time_for_changes": "insufficient_data", "change_failure_rate": cfr, "mean_time_to_recovery": mttr}

@releases_router.post("/{release_id}/approvals", response_model=ReleaseApprovalResponse)
def request_approval(release_id: UUID, payload: ReleaseApprovalCreate, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    
    approval = ReleaseApproval(
        organization_id=org_id,
        release_id=release_id,
        requested_by_id=current_user.id,
        reviewer_id=payload.reviewer_id,
        comment=payload.comment,
        status=ReleaseApprovalStatus.PENDING
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    record_event(db, org_id, "RELEASE_APPROVAL_REQUESTED", "RELEASE", actor_user_id=current_user.id, entity_id=release_id)
    return approval

@releases_router.post("/approvals/{approval_id}/approve", response_model=ReleaseApprovalResponse)
def approve_release(approval_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    approval = db.query(ReleaseApproval).filter(ReleaseApproval.id == approval_id, ReleaseApproval.organization_id == org_id).first()
    if not approval: raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.reviewer_id != current_user.id:
        deps.require_organization_member(db, current_user.id, org_id)
        
    approval.status = ReleaseApprovalStatus.APPROVED
    
    release = db.query(Release).filter(Release.id == approval.release_id).first()
    if release:
        release.status = ReleaseStatus.APPROVED
        release.approved_by_id = current_user.id
        
    db.commit()
    db.refresh(approval)
    
    record_event(db, org_id, "RELEASE_APPROVED", "RELEASE", actor_user_id=current_user.id, entity_id=approval.release_id)
    return approval

@releases_router.post("/approvals/{approval_id}/reject", response_model=ReleaseApprovalResponse)
def reject_release(approval_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    approval = db.query(ReleaseApproval).filter(ReleaseApproval.id == approval_id, ReleaseApproval.organization_id == org_id).first()
    if not approval: raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.reviewer_id != current_user.id:
        deps.require_organization_member(db, current_user.id, org_id)
        
    approval.status = ReleaseApprovalStatus.REJECTED
    
    release = db.query(Release).filter(Release.id == approval.release_id).first()
    if release:
        release.status = ReleaseStatus.READY
        
    db.commit()
    db.refresh(approval)
    
    record_event(db, org_id, "RELEASE_REJECTED", "RELEASE", actor_user_id=current_user.id, entity_id=approval.release_id)
    return approval

@releases_router.post("/approvals/{approval_id}/revoke", response_model=ReleaseApprovalResponse)
def revoke_approval(approval_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    approval = db.query(ReleaseApproval).filter(ReleaseApproval.id == approval_id, ReleaseApproval.organization_id == org_id).first()
    if not approval: raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.requested_by_id != current_user.id:
        deps.require_organization_member(db, current_user.id, org_id)
        
    approval.status = ReleaseApprovalStatus.REVOKED
    db.commit()
    db.refresh(approval)
    
    record_event(db, org_id, "RELEASE_APPROVAL_REVOKED", "RELEASE", actor_user_id=current_user.id, entity_id=approval.release_id)
    return approval

@environments_router.get("/{env_id}/health")
def get_environment_health(env_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    env = db.query(Environment).filter(Environment.id == env_id, Environment.organization_id == org_id).first()
    if not env: raise HTTPException(status_code=404, detail="Environment not found")
    
    status = ReleaseEngine.check_environment_health(db, str(env.id))
    return {"status": status}

@releases_router.post("/{release_id}/promote", response_model=ReleaseResponse)
def promote_release(release_id: UUID, target_env: str, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    
    # Simple promote logic: just change target environment
    release.target_environment = target_env
    release.status = ReleaseStatus.READY
    db.commit()
    db.refresh(release)
    
    record_event(db, org_id, "RELEASE_PROMOTED", "RELEASE", actor_user_id=current_user.id, entity_id=release.id, metadata={"target_env": target_env})
    return release

@releases_router.post("/{release_id}/rollback", response_model=ReleaseResponse)
def rollback_release(release_id: UUID, db: Session = Depends(deps.get_db), current_user: User = Depends(deps.get_current_user), org_id: UUID = Depends(deps.get_current_organization_id)):
    deps.require_organization_member(db, current_user.id, org_id)
    release = db.query(Release).filter(Release.id == release_id, Release.organization_id == org_id).first()
    if not release: raise HTTPException(status_code=404, detail="Release not found")
    
    release.status = ReleaseStatus.ROLLED_BACK
    from datetime import datetime
    import pytz
    release.rollback_timestamp = datetime.now(pytz.utc)
    db.commit()
    db.refresh(release)
    
    record_event(db, org_id, "RELEASE_ROLLED_BACK", "RELEASE", actor_user_id=current_user.id, entity_id=release.id)
    return release
