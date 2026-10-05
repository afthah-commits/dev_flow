
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime

from app.api import deps
from app.models.user import User
from app.schemas.analytics import (
    DashboardOverview, ProjectAnalyticsResponse, GitHubAnalyticsResponse,
    ExecutiveAnalyticsResponse, TeamAnalyticsResponse, SprintAnalyticsResponse,
    DeliveryAnalyticsResponse, TimeAnalyticsResponse, WorkflowAnalyticsResponse,
    AutomationAnalyticsResponse, ClientAnalyticsResponse, KnowledgeAnalyticsResponse,
    CollaborationAnalyticsResponse, UsageAnalyticsResponse,
    AnalyticsQueryRequest, AnalyticsQueryResponse
)
from app.services.analytics_service import (
    get_dashboard_overview, get_project_analytics, get_executive_analytics,
    get_team_analytics, get_sprint_analytics, get_delivery_analytics,
    get_time_analytics, get_workflow_analytics, get_automation_analytics,
    get_client_analytics, get_knowledge_analytics, get_collaboration_analytics,
    get_usage_analytics, execute_analytics_query
)
from app.api.v1.reports import check_permission

router = APIRouter()

@router.get("/dashboard", response_model=DashboardOverview)
def get_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_dashboard_overview(db, org_id)

@router.get("/executive", response_model=ExecutiveAnalyticsResponse)
def get_executive_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.executive")
    return get_executive_analytics(db, org_id, date_from, date_to)

@router.get("/projects/{project_id}", response_model=ProjectAnalyticsResponse)
def get_project_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: UUID
) -> Any:
    from app.models.project import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    member = deps.require_organization_member(db, current_user.id, UUID(project.organization_id))
    check_permission(db, member, "analytics.projects")
    return get_project_analytics(db, project_id)

@router.get("/teams/{team_id}", response_model=TeamAnalyticsResponse)
def get_team_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    team_id: UUID,
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.teams")
    return get_team_analytics(db, team_id, org_id)

@router.get("/sprints/{sprint_id}", response_model=SprintAnalyticsResponse)
def get_sprint_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    sprint_id: UUID,
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.projects")
    return get_sprint_analytics(db, sprint_id, org_id)

@router.get("/delivery", response_model=DeliveryAnalyticsResponse)
def get_delivery_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_delivery_analytics(db, org_id)

@router.get("/productivity", response_model=TimeAnalyticsResponse)
def get_time_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_time_analytics(db, org_id)

@router.get("/workflow", response_model=WorkflowAnalyticsResponse)
def get_workflow_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_workflow_analytics(db, org_id)

@router.get("/automation", response_model=AutomationAnalyticsResponse)
def get_automation_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_automation_analytics(db, org_id)

@router.get("/clients", response_model=ClientAnalyticsResponse)
def get_client_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_client_analytics(db, org_id)

@router.get("/knowledge", response_model=KnowledgeAnalyticsResponse)
def get_knowledge_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_knowledge_analytics(db, org_id)

@router.get("/collaboration", response_model=CollaborationAnalyticsResponse)
def get_collaboration_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_collaboration_analytics(db, org_id)

@router.get("/usage", response_model=UsageAnalyticsResponse)
def get_usage_analytics_api(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    return get_usage_analytics(db, org_id)

@router.post("/query", response_model=AnalyticsQueryResponse)
def query_analytics_api(
    *,
    request: AnalyticsQueryRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.view")
    
    ALLOWED_METRICS = [
        "tasks.completed", "tasks.overdue", "sprint.velocity",
        "time.tracked_hours", "deployments.success_rate",
        "releases.count", "workflows.success_rate",
        "projects.count"
    ]
    
    if request.metric not in ALLOWED_METRICS:
        raise HTTPException(status_code=400, detail="Unknown metric")
        
    return execute_analytics_query(db, org_id, request)


@router.post("/export")
def export_analytics_data(
    *,
    request: AnalyticsQueryRequest,
    format: str = Query("csv"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
) -> Any:
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Organization-Id header missing")
    member = deps.require_organization_member(db, current_user.id, org_id)
    check_permission(db, member, "analytics.export")
    
    # Reuse query executor
    result = execute_analytics_query(db, org_id, request)
    
    # Note: the real DevFlow export engine uses StreamingResponse, 
    # but here we follow Phase 18 Report export which returns JSON payload with format
    return {"data": result.data, "format": format}
