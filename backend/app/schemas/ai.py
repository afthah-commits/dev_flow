from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class AIMessageBase(BaseModel):
    role: str
    content: str

class AIMessageCreate(AIMessageBase):
    pass

class AIMessageResponse(AIMessageBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

class AIConversationBase(BaseModel):
    title: str
    project_id: Optional[UUID] = None

class AIConversationCreate(AIConversationBase):
    pass

class AIConversationResponse(AIConversationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: Optional[List[AIMessageResponse]] = None
    
    class Config:
        from_attributes = True

class AIChatRequest(BaseModel):
    message: str

class AIProjectSummaryRequest(BaseModel):
    pass

class AINextTaskRequest(BaseModel):
    pass

class AITaskDescriptionRequest(BaseModel):
    instruction: str

class AITaskBreakdownRequest(BaseModel):
    task_id: UUID

class AIReadmeRequest(BaseModel):
    pass

class TaskSuggestion(BaseModel):
    title: str
    description: str
    priority: str
    labels: List[str]

class TaskBreakdown(BaseModel):
    subtasks: List[TaskSuggestion]

class AIActionResponse(BaseModel):
    result: str
    structured_data: Optional[dict] = None


# ---------------------------------------------------------------------------
# Phase 47 — AI-assisted planning & estimation (advisory only)
# ---------------------------------------------------------------------------

class AIPlanningRequest(BaseModel):
    task_id: Optional[UUID] = None

class AIPlanningSuggestion(BaseModel):
    title: str
    description: str = ""
    priority: str = "MEDIUM"
    # Phase 48 — progressive (multi-level) breakdown fields. A flat
    # Phase 47 suggestion is still valid (level defaults to 0, no parent,
    # no children, no per-suggestion estimate).
    suggestion_id: Optional[str] = None
    estimated_points: Optional[float] = None
    level: int = 0
    parent_suggestion_id: Optional[str] = None
    children: Optional[List["AIPlanningSuggestion"]] = None

    @field_validator("estimated_points", mode="before")
    @classmethod
    def _reject_boolean_points(cls, v):
        # Phase 49: pydantic lax mode would coerce booleans to numbers;
        # user/AI supplied booleans are invalid input, reject them before
        # coercion runs.
        if isinstance(v, bool):
            raise ValueError("estimated_points must be a number, not a boolean")
        return v

class AIPlanningCapacity(BaseModel):
    status: str  # OK | OVER_CAPACITY | INSUFFICIENT_DATA
    sprint_id: Optional[UUID] = None
    sprint_name: Optional[str] = None
    capacity_points: Optional[float] = None
    committed_points: Optional[float] = None
    remaining_points: Optional[float] = None

class AIPlanningAnalysis(BaseModel):
    """Advisory AI planning output. Never applied automatically."""
    task_id: Optional[UUID] = None
    project_id: UUID
    complexity: str  # LOW | MEDIUM | HIGH
    complexity_factors: List[str]
    estimate_points: float
    estimate_confidence: str  # HIGH | MEDIUM | LOW
    estimate_factors: List[str]
    risks: List[str]
    missing_information: List[str]
    dependency_concerns: List[str]
    suggested_breakdown: List[AIPlanningSuggestion]
    capacity: Optional[AIPlanningCapacity] = None
    advisory: bool = True
    provider: str = ""

class AIPlanningApplyRequest(BaseModel):
    task_id: UUID
    suggestions: List[AIPlanningSuggestion]


class ProjectSummary(BaseModel):
    current_status: str
    progress: str
    health: str
    major_completed_work: List[str]
    overdue_work: List[str]
    blockers: List[str]
    sprint_status: str
    github_activity: str
    deployment_status: str
    risks: List[str]
    recommended_next_actions: List[str]

class ProjectRisk(BaseModel):
    title: str
    severity: str
    category: str
    explanation: str
    evidence: List[str]
    recommendation: str

class TaskPrioritySuggestion(BaseModel):
    task_id: UUID
    task_key: str
    priority: str
    score: float
    reason: str
    blockers: List[str]
    recommendation: str

class SprintPlan(BaseModel):
    recommended_tasks: List[UUID]
    estimated_workload: str
    risks: List[str]
    expected_sprint_outcome: str
    excluded_tasks_with_reasons: dict

class GitHubSummary(BaseModel):
    recent_development_summary: str
    pr_activity: str
    issue_trends: str
    potential_risks: List[str]
    stale_prs: List[str]
    unresolved_issues: List[str]
    engineering_activity: str

class ChangeIntelligence(BaseModel):
    change_summary: str
    affected_areas: List[str]
    possible_risks: List[str]
    testing_recommendations: List[str]

class ReleaseAnalysis(BaseModel):
    release_summary: str
    completed_work: List[str]
    incomplete_tasks: List[str]
    pr_summary: str
    deployment_readiness: str
    blockers: List[str]
    risks: List[str]
    recommended_checks: List[str]

class DeploymentAnalysis(BaseModel):
    deployment_health: str
    recurring_failures: List[str]
    likely_risk_areas: List[str]
    recommended_checks: List[str]

class DailyEngineeringBrief(BaseModel):
    completed_yesterday: List[str]
    active_today: List[str]
    overdue: List[str]
    blocked: List[str]
    github_changes: str
    pr_activity: str
    deployment_changes: str
    important_risks: List[str]
    recommended_focus: str

class AIProjectMemoryCreate(BaseModel):
    category: str
    key: str
    value: str

class AIProjectMemoryResponse(AIProjectMemoryCreate):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class AIUsageResponse(BaseModel):
    id: UUID
    provider: str
    model: str
    request_type: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ForecastAssumptions(BaseModel):
    velocity_tasks_per_week: float
    velocity_story_points_per_week: float
    historical_weeks_analyzed: int
    unestimated_tasks: int

class ProjectForecast(BaseModel):
    project_id: UUID
    estimated_completion_date: Optional[datetime] = None
    remaining_tasks: int
    completed_tasks: int
    completion_rate: float
    velocity: float # tasks per sprint/week
    remaining_story_points: float
    estimated_sprints_remaining: Optional[int] = None
    confidence: str # HIGH, MEDIUM, LOW
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    assumptions: ForecastAssumptions

class RiskItem(BaseModel):
    category: str
    severity: str
    score: int
    title: str
    explanation: str
    evidence: str
    recommendation: str

class ProjectRiskEngineResult(BaseModel):
    overall_risk_score: int
    risk_level: str
    risks: List[RiskItem]

class SprintCapacityRecommendation(BaseModel):
    recommended_capacity_points: float
    suggested_tasks: List[UUID]
    excluded_tasks: List[UUID]
    reasons_for_exclusions: dict # task_id string to reason
    overloaded_members: List[UUID]
    dependency_warnings: List[str]
    confidence: str

class ProjectHealthReport(BaseModel):
    executive_summary: str
    project_health: str
    delivery_status: str
    engineering_risks: str
    team_workload: str
    github_activity: str
    deployment_health: str
    productivity: str
    recommendations: List[str]
    next_actions: List[str]

class OrgDailyBriefItem(BaseModel):
    title: str
    priority: str
    reason: str
    source: str

class OrgDailyBrief(BaseModel):
    projects_needing_attention: List[str]
    overdue_tasks: List[OrgDailyBriefItem]
    blocked_tasks: List[OrgDailyBriefItem]
    sprint_deadlines: List[OrgDailyBriefItem]
    deployment_failures: List[OrgDailyBriefItem]
    important_github_activity: List[OrgDailyBriefItem]
    security_events: List[OrgDailyBriefItem]
    failed_background_jobs: List[OrgDailyBriefItem]
    high_priority_notifications: List[OrgDailyBriefItem]
    recommended_focus_for_today: List[OrgDailyBriefItem]

class TaskPriorityScore(BaseModel):
    task_id: UUID
    task_key: str
    score: float
    priority_level: str
    reasons: List[str]

# Phase 27
class AIKnowledgeAsk(BaseModel):
    question: str
    space_id: Optional[UUID] = None
    project_id: Optional[UUID] = None

class AIKnowledgeAnswer(BaseModel):
    answer: str
    sources: List[str]
    confidence: str

class AIKnowledgeSummary(BaseModel):
    summary: str
    key_points: List[str]
    risks: List[str]
    related_topics: List[str]
