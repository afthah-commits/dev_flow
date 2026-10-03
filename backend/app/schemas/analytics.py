from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class DashboardOverview(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    open_github_prs: Optional[int] = None
    open_github_issues: Optional[int] = None

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
    due_soon: int # within 3 days
    future: int
    no_deadline: int

class TaskTrendItem(BaseModel):
    date: str
    created: int
    completed: int
    overdue: int

class ProjectAnalyticsResponse(BaseModel):
    completion_rate: float
    total_tasks: int
    completed: int
    in_progress: int
    overdue: int
    health: ProjectHealth
    status_distribution: List[TaskStatusDistribution]
    priority_distribution: List[TaskPriorityDistribution]
    deadlines: DeadlineAnalysis
    trends: List[TaskTrendItem]

class GitHubAnalyticsResponse(BaseModel):
    recent_commits: int
    open_prs: int
    closed_prs: int
    open_issues: int
    closed_issues: int
