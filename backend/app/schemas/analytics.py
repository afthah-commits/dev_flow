
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID

class DashboardOverview(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    overdue_tasks: int = 0
    open_github_prs: Optional[int] = None
    open_github_issues: Optional[int] = None

class ExecutiveAnalyticsResponse(BaseModel):
    active_projects: int = 0
    completed_projects: int = 0
    open_tasks: int = 0
    overdue_tasks: int = 0
    active_sprints: int = 0
    sprint_completion_percent: float = 0
    delivery_rate: float = 0
    deployment_success_rate: float = 0
    failed_deployments: int = 0
    average_cycle_time_hours: float = 0
    average_lead_time_hours: float = 0
    team_workload_percent: float = 0
    time_tracking_compliance: float = 0
    active_workflow_executions: int = 0
    client_request_status: Dict[str, int] = {}
    automation_success_rate: float = 0

class ProjectHealth(BaseModel):
    score: int
    status: str

class TaskStatusDistribution(BaseModel):
    status: str
    count: int

class TaskPriorityDistribution(BaseModel):
    priority: str
    count: int

class DeadlineAnalysis(BaseModel):
    overdue: int
    due_today: int
    due_soon: int
    future: int
    no_deadline: int

class TaskTrendItem(BaseModel):
    date: str
    created: int
    completed: int
    overdue: int

class ProjectAnalyticsResponse(BaseModel):
    completion_rate: float = 0
    total_tasks: int = 0
    completed: int = 0
    in_progress: int = 0
    overdue: int = 0
    health: ProjectHealth
    status_distribution: List[TaskStatusDistribution] = []
    priority_distribution: List[TaskPriorityDistribution] = []
    deadlines: DeadlineAnalysis
    trends: List[TaskTrendItem] = []
    
    # Phase 33 additions
    sprint_progress: float = 0
    velocity: float = 0
    estimate_vs_actual: Dict[str, float] = {}
    blockers: int = 0
    cycle_time: float = 0
    deployment_frequency: int = 0
    deployment_success: float = 0

class GitHubAnalyticsResponse(BaseModel):
    recent_commits: int
    open_prs: int
    closed_prs: int
    open_issues: int
    closed_issues: int
    # Phase 42: optional non-breaking status. "ok" = live/cached GitHub data
    # (or a genuinely empty repo); "unavailable" = GitHub-side failure, so the
    # UI can show a degraded warning instead of misleading zeros. Absence of
    # the field in old payloads is treated as "ok" by existing consumers.
    status: Optional[str] = "ok"

class TeamAnalyticsResponse(BaseModel):
    member_count: int = 0
    assigned_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    workload: float = 0
    estimated_hours: float = 0
    actual_hours: float = 0
    sprint_points: float = 0
    completion_rate: float = 0
    average_cycle_time: float = 0
    time_tracking_compliance: float = 0

class SprintAnalyticsResponse(BaseModel):
    velocity: float = 0
    planned_points: float = 0
    completed_points: float = 0
    remaining_points: float = 0
    burndown: List[Dict[str, Any]] = []
    burnup: List[Dict[str, Any]] = []
    scope_changes: int = 0
    blocked_tasks: int = 0
    average_completion_time: float = 0

class DeliveryAnalyticsResponse(BaseModel):
    deployment_frequency: float = 0
    lead_time_for_changes: float = 0
    change_failure_rate: float = 0
    mean_time_to_recovery: float = 0
    successful_deployments: int = 0
    failed_deployments: int = 0
    rollbacks: int = 0
    deployment_duration: float = 0

class TimeAnalyticsResponse(BaseModel):
    tracked_hours: float = 0
    estimated_hours: float = 0
    variance: float = 0
    tracking_compliance: float = 0
    active_days: int = 0
    weekly_trend: List[Dict[str, Any]] = []
    project_distribution: Dict[str, float] = {}

class WorkflowAnalyticsResponse(BaseModel):
    active_workflows: int = 0
    executions: int = 0
    success_rate: float = 0
    failed_executions: int = 0
    average_execution_time: float = 0
    blocked_executions: int = 0

class AutomationAnalyticsResponse(BaseModel):
    active_automations: int = 0
    triggered_executions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    skipped_actions: int = 0

class ClientAnalyticsResponse(BaseModel):
    active_clients: int = 0
    client_projects: int = 0
    client_requests: int = 0
    pending_requests: int = 0
    completed_requests: int = 0
    response_time: float = 0

class KnowledgeAnalyticsResponse(BaseModel):
    spaces: int = 0
    documents: int = 0
    document_views: int = 0
    active_authors: int = 0
    stale_documents: int = 0

class CollaborationAnalyticsResponse(BaseModel):
    comments: int = 0
    discussions: int = 0
    mentions: int = 0
    reactions: int = 0
    active_contributors: int = 0

class UsageAnalyticsResponse(BaseModel):
    members: int = 0
    teams: int = 0
    projects: int = 0
    api_requests: int = 0
    automation_usage: int = 0
    workflow_usage: int = 0
    job_executions: int = 0
    deployments: int = 0

class AnalyticsQueryRequest(BaseModel):
    metric: str
    dimensions: List[str] = []
    filters: Dict[str, Any] = {}
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    group_by: Optional[str] = None
    sort_by: Optional[str] = None

class AnalyticsQueryResponse(BaseModel):
    metric: str
    data: List[Dict[str, Any]]
