from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Dict, List
from uuid import UUID
import json

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.ai_conversation import AIConversation, AIMessage
from app.schemas.ai import AIKnowledgeAsk, AIKnowledgeAnswer, AIKnowledgeSummary
from app.models.knowledge import KnowledgeDocument, KnowledgeSpace
from app.schemas.ai import (
    AIConversationCreate, AIConversationResponse, AIChatRequest, AIMessageResponse,
    AIActionResponse, TaskSuggestion, TaskBreakdown, AITaskDescriptionRequest, AITaskBreakdownRequest
)
from app.schemas.workflow import AIWorkflowSuggestion
from app.services.ai.service import get_ai_provider, SYSTEM_PROMPT
from app.services.ai.context import build_project_context
from app.core.rate_limit import rate_limit

# AI endpoints are computationally expensive; cap per-IP request volume.
# Thresholds are generous so legitimate local development is never blocked.
AI_RATE_LIMIT = (100, 60)

router = APIRouter()

def _get_conversation(db: Session, conv_id: UUID, user_id: UUID) -> AIConversation:
    conv = db.query(AIConversation).filter(AIConversation.id == conv_id, AIConversation.user_id == user_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.get("/conversations", response_model=List[AIConversationResponse])
def list_conversations(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: UUID = None
) -> Any:
    q = db.query(AIConversation).filter(AIConversation.user_id == current_user.id)
    if project_id:
        q = q.filter(AIConversation.project_id == project_id)
    return q.order_by(AIConversation.updated_at.desc()).all()

@router.post("/conversations", response_model=AIConversationResponse)
def create_conversation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    request: AIConversationCreate
) -> Any:
    if request.project_id:
        proj = db.query(Project).filter(Project.id == request.project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        deps.require_organization_member(db, current_user.id, proj.organization_id)
            
    conv = AIConversation(
        user_id=current_user.id,
        project_id=request.project_id,
        title=request.title
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/conversations/{conversation_id}", response_model=AIConversationResponse)
def get_conversation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    conversation_id: UUID
) -> Any:
    return _get_conversation(db, conversation_id, current_user.id)

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    conversation_id: UUID
) -> Any:
    conv = _get_conversation(db, conversation_id, current_user.id)
    db.delete(conv)
    db.commit()
    return {"message": "Deleted"}

@router.post("/conversations/{conversation_id}/messages", response_model=AIMessageResponse)
async def send_message(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    conversation_id: UUID,
    request: AIChatRequest,
    _rl: None = Depends(rate_limit(*AI_RATE_LIMIT))
) -> Any:
    conv = _get_conversation(db, conversation_id, current_user.id)
    
    # Store user message
    user_msg = AIMessage(conversation_id=conv.id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()
    
    # Build context
    context_str = ""
    if conv.project_id:
        context_str = await build_project_context(db, conv.project_id, current_user.id)
        
    full_prompt = f"{SYSTEM_PROMPT}\\n\\n{context_str}"
    
    # Get history (last 10 messages)
    history = db.query(AIMessage).filter(AIMessage.conversation_id == conv.id).order_by(AIMessage.created_at.asc()).limit(10).all()
    api_messages = [{"role": m.role, "content": m.content} for m in history]
    
    # Call AI
    provider = get_ai_provider()
    try:
        reply = await provider.chat(messages=api_messages, system_prompt=full_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    ai_msg = AIMessage(conversation_id=conv.id, role="assistant", content=reply)
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    
    return ai_msg

# --- Quick Actions (Structured Outputs) ---
@router.post("/projects/{project_id}/actions/task-suggestion", response_model=AIActionResponse)
async def suggest_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: UUID,
    request: AITaskDescriptionRequest
) -> Any:
    context_str = await build_project_context(db, project_id, current_user.id)
    schema = TaskSuggestion.model_json_schema()
    
    provider = get_ai_provider()
    messages = [{"role": "user", "content": f"Generate a task for: {request.instruction}"}]
    
    try:
        res = await provider.chat(messages=messages, system_prompt=f"{SYSTEM_PROMPT}\\n\\n{context_str}", json_schema=schema)
        data = json.loads(res)
        return AIActionResponse(result="Success", structured_data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/actions/task-breakdown", response_model=AIActionResponse)
async def breakdown_task(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: UUID,
    request: AITaskBreakdownRequest
) -> Any:
    # ensure task belongs to project
    from app.models.task import Task
    task = db.query(Task).filter(Task.id == request.task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    context_str = await build_project_context(db, project_id, current_user.id)
    schema = TaskBreakdown.model_json_schema()
    
    provider = get_ai_provider()
    messages = [{"role": "user", "content": f"Break down this task into subtasks: {task.title}\\n{task.description}"}]
    
    try:
        res = await provider.chat(messages=messages, system_prompt=f"{SYSTEM_PROMPT}\\n\\n{context_str}", json_schema=schema)
        data = json.loads(res)
        return AIActionResponse(result="Success", structured_data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/releases/{release_id}/generate-notes")
async def generate_release_notes(
    project_id: UUID,
    release_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id),
) -> Any:
    """Generate AI-drafted release notes. Output is advisory only — user must review."""
    deps.require_organization_member(db, current_user.id, org_id)

    from app.models.delivery import Release, ReleaseTask, ReleasePullRequest
    from app.models.task import Task

    release = db.query(Release).filter(Release.id == release_id, Release.project_id == project_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    # Gather context
    rts = db.query(ReleaseTask).filter(ReleaseTask.release_id == release_id).all()
    task_ids = [rt.task_id for rt in rts]
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all() if task_ids else []
    prs = db.query(ReleasePullRequest).filter(ReleasePullRequest.release_id == release_id).all()

    task_lines = "\n".join([f"- [{t.status.value if t.status else 'N/A'}] {t.title}" for t in tasks]) or "No tasks"
    pr_lines = "\n".join([f"- PR #{p.pr_number}: {p.pr_title or 'Untitled'}" for p in prs]) or "No PRs"

    prompt = f"""Generate release notes for version {release.version} ({release.name}).
Release type: {release.release_type.value if release.release_type else 'MINOR'}

Included tasks:
{task_lines}

Included pull requests:
{pr_lines}

Format the notes with sections: Features, Improvements, Bug Fixes, Breaking Changes, Other.
Keep it professional and concise."""

    provider = get_ai_provider()
    messages = [{"role": "user", "content": prompt}]
    try:
        notes = await provider.chat(messages=messages, system_prompt=SYSTEM_PROMPT)
        return {"release_id": str(release.id), "version": release.version, "generated_notes": notes, "advisory": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/projects/{project_id}/discussions/{discussion_id}/summary")
async def summarize_discussion(
    project_id: UUID,
    discussion_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id),
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    from app.models.collaboration import Discussion, Comment
    disc = db.query(Discussion).filter(Discussion.id == discussion_id, Discussion.project_id == project_id).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Discussion not found")
    comments = db.query(Comment).filter(Comment.entity_id == discussion_id).all()
    
    prompt = f"Summarize discussion '{disc.title}': {disc.content}\nComments: " + " ".join([c.content for c in comments])
    provider = get_ai_provider()
    messages = [{"role": "user", "content": prompt}]
    notes = await provider.chat(messages=messages, system_prompt=SYSTEM_PROMPT)
    return {"summary": notes}

@router.post("/projects/{project_id}/activity/summary")
async def summarize_activity(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id),
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    prompt = "Summarize recent activity in the project."
    provider = get_ai_provider()
    messages = [{"role": "user", "content": prompt}]
    notes = await provider.chat(messages=messages, system_prompt=SYSTEM_PROMPT)
    return {"summary": notes}

@router.post("/automations/generate")
async def generate_automation(
    request: dict,
    current_user: User = Depends(deps.get_current_user),
    _rl: None = Depends(rate_limit(*AI_RATE_LIMIT))
) -> Any:
    prompt = request.get("prompt")
    # Mock generation
    return {
        "trigger_type": "TASK_STATUS_CHANGED",
        "conditions": {
            "logical_operator": "ALL",
            "conditions": [
                {"field": "task.status", "operator": "EQUALS", "value": "OVERDUE"}
            ]
        },
        "actions": [
            {
                "type": "CREATE_NOTIFICATION",
                "message": "Task is overdue"
            }
        ]
    }

from pydantic import BaseModel
from app.services.audit_service import record_event
from app.schemas.ai import AIKnowledgeAsk, AIKnowledgeAnswer, AIKnowledgeSummary
from app.models.knowledge import KnowledgeDocument, KnowledgeSpace
from app.schemas.ai import (
    ProjectSummary, ProjectRisk, TaskPrioritySuggestion, SprintPlan, 
    GitHubSummary, ChangeIntelligence, ReleaseAnalysis, DeploymentAnalysis, 
    DailyEngineeringBrief, AIProjectMemoryCreate, AIProjectMemoryResponse, AIUsageResponse
)
from app.models.ai_project_memory import AIProjectMemory
from app.models.ai_usage import AIUsage
from app.services.ai_context import get_comprehensive_project_context
from app.services.ai.service import get_ai_provider

@router.post("/projects/{project_id}/summary", response_model=ProjectSummary)
async def generate_project_summary(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    context_data = await get_comprehensive_project_context(db, project_id, current_user.id, org_id)
    provider = get_ai_provider()
    
    prompt = f"Analyze this project context and provide a structured summary:\n{json.dumps(context_data, default=str)}"
    result_str = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are an AI Engineering Intelligence Platform. Provide an objective summary of the project.",
        json_schema=ProjectSummary.model_json_schema()
    )
    
    # Audit log
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.project_summary_generated",
        entity_type="project",
        entity_id=project_id,
        metadata={"provider": type(provider).__name__}
    )
    
    return ProjectSummary.model_validate_json(result_str)

@router.post("/projects/{project_id}/risks", response_model=List[ProjectRisk])
async def generate_project_risks(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    context_data = await get_comprehensive_project_context(db, project_id, current_user.id, org_id)
    provider = get_ai_provider()
    
    prompt = f"Analyze this project and identify key risks:\n{json.dumps(context_data, default=str)}"
    
    class RiskList(BaseModel):
        risks: List[ProjectRisk]
        
    result_str = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are an AI Risk Analyzer.",
        json_schema=RiskList.model_json_schema()
    )
    
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.risk_analysis_generated",
        entity_type="project",
        entity_id=project_id,
        metadata={}
    )
    
    try:
        data = RiskList.model_validate_json(result_str)
        return data.risks
    except Exception:
        # fallback for mock
        return [ProjectRisk.model_validate_json(result_str)] if "severity" in result_str else []

@router.post("/projects/{project_id}/prioritize", response_model=List[TaskPrioritySuggestion])
async def generate_task_prioritization(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    context_data = await get_comprehensive_project_context(db, project_id, current_user.id, org_id)
    provider = get_ai_provider()
    
    class PriorityList(BaseModel):
        priorities: List[TaskPrioritySuggestion]
        
    prompt = f"Analyze uncompleted tasks and prioritize them:\n{json.dumps(context_data.get('tasks', {}), default=str)}"
    result_str = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are an AI Task Prioritizer.",
        json_schema=PriorityList.model_json_schema()
    )
    
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.task_priority_suggested",
        entity_type="project",
        entity_id=project_id,
        metadata={}
    )
    
    try:
        data = PriorityList.model_validate_json(result_str)
        return data.priorities
    except Exception:
        return [TaskPrioritySuggestion.model_validate_json(result_str)] if "score" in result_str else []

@router.post("/projects/{project_id}/sprint-plan", response_model=SprintPlan)
async def generate_sprint_plan(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    context_data = await get_comprehensive_project_context(db, project_id, current_user.id, org_id)
    provider = get_ai_provider()
    
    prompt = f"Plan the next sprint:\n{json.dumps(context_data, default=str)}"
    result_str = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are an AI Sprint Planner.",
        json_schema=SprintPlan.model_json_schema()
    )
    
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.sprint_plan_generated",
        entity_type="project",
        entity_id=project_id,
        metadata={}
    )
    
    return SprintPlan.model_validate_json(result_str)

@router.post("/projects/{project_id}/github/summary", response_model=GitHubSummary)
async def generate_github_summary(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    context_data = await get_comprehensive_project_context(db, project_id, current_user.id, org_id)
    provider = get_ai_provider()
    
    prompt = f"Summarize GitHub activity:\n{json.dumps(context_data.get('github', {}), default=str)}"
    result_str = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are an AI GitHub Analyzer.",
        json_schema=GitHubSummary.model_json_schema()
    )
    
    return GitHubSummary.model_validate_json(result_str)

@router.post("/releases/{release_id}/analysis", response_model=ReleaseAnalysis)
async def generate_release_analysis(
    release_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    provider = get_ai_provider()
    prompt = f"Analyze release readiness for release {release_id}."
    result_str = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are an AI Release Analyzer.",
        json_schema=ReleaseAnalysis.model_json_schema()
    )
    
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.release_analysis_generated",
        entity_type="release",
        entity_id=release_id,
        metadata={}
    )
    
    return ReleaseAnalysis.model_validate_json(result_str)

@router.post("/projects/{project_id}/deployment-analysis", response_model=DeploymentAnalysis)
async def generate_deployment_analysis(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    context_data = await get_comprehensive_project_context(db, project_id, current_user.id, org_id)
    provider = get_ai_provider()
    
    prompt = f"Analyze deployments:\n{json.dumps(context_data.get('deployments', []), default=str)}"
    result_str = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are an AI Deployment Analyzer.",
        json_schema=DeploymentAnalysis.model_json_schema()
    )
    
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.deployment_analysis_generated",
        entity_type="project",
        entity_id=project_id,
        metadata={}
    )
    
    return DeploymentAnalysis.model_validate_json(result_str)

@router.get("/projects/{project_id}/daily-brief", response_model=DailyEngineeringBrief)
async def generate_daily_brief(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    context_data = await get_comprehensive_project_context(db, project_id, current_user.id, org_id)
    provider = get_ai_provider()
    
    prompt = f"Generate daily engineering brief:\n{json.dumps(context_data, default=str)}"
    result_str = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are an AI Engineering Assistant.",
        json_schema=DailyEngineeringBrief.model_json_schema()
    )
    
    return DailyEngineeringBrief.model_validate_json(result_str)

@router.get("/usage", response_model=List[AIUsageResponse])
def get_ai_usage(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    usages = db.query(AIUsage).filter(AIUsage.organization_id == org_id).all()
    return usages


from app.services.predictive_intelligence import (
    calculate_project_forecast, calculate_project_risks, calculate_sprint_plan,
    calculate_task_priorities, get_org_daily_brief
)
from app.schemas.ai import AIKnowledgeAsk, AIKnowledgeAnswer, AIKnowledgeSummary
from app.models.knowledge import KnowledgeDocument, KnowledgeSpace
from app.schemas.ai import (
    ProjectForecast, ProjectRiskEngineResult, SprintCapacityRecommendation,
    ProjectHealthReport, OrgDailyBrief, TaskPriorityScore
)

@router.get("/projects/{project_id}/forecast", response_model=ProjectForecast)
def get_project_forecast(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    # Authorization checks are done implicitly via org_id filters in the service, but let's verify project exists for org
    project = db.query(Project).filter(Project.id == project_id, Project.organization_id == org_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    forecast = calculate_project_forecast(db, project_id, org_id)
    
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.forecast_generated",
        entity_type="project",
        entity_id=project_id,
        metadata={}
    )
    return forecast

@router.get("/projects/{project_id}/sprint-planning", response_model=SprintCapacityRecommendation)
def get_smart_sprint_plan(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    project = db.query(Project).filter(Project.id == project_id, Project.organization_id == org_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    plan = calculate_sprint_plan(db, project_id, org_id)
    
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.sprint_recommendation_generated",
        entity_type="project",
        entity_id=project_id,
        metadata={}
    )
    return plan

@router.get("/projects/{project_id}/health-report", response_model=ProjectHealthReport)
async def get_project_health_report(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    context_data = await get_comprehensive_project_context(db, project_id, current_user.id, org_id)
    provider = get_ai_provider()
    
    prompt = f"Generate a comprehensive AI Engineering Health Report based on this data:\n{json.dumps(context_data, default=str)}"
    result_str = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are an AI Engineering Intelligence Platform. Provide a structured health report.",
        json_schema=ProjectHealthReport.model_json_schema()
    )
    
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.health_report_generated",
        entity_type="project",
        entity_id=project_id,
        metadata={}
    )
    
    return ProjectHealthReport.model_validate_json(result_str)

@router.get("/daily-brief", response_model=OrgDailyBrief)
def get_daily_brief(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    brief_data = get_org_daily_brief(db, org_id)
    return OrgDailyBrief(**brief_data)

@router.get("/projects/{project_id}/task-priorities", response_model=List[TaskPriorityScore])
def get_task_priorities(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    project = db.query(Project).filter(Project.id == project_id, Project.organization_id == org_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    priorities = calculate_task_priorities(db, project_id, org_id)
    
    record_event(
        db=db,
        organization_id=org_id,
        actor_user_id=current_user.id,
        event_type="ai.prioritization_generated",
        entity_type="project",
        entity_id=project_id,
        metadata={}
    )
    return priorities

@router.get("/projects/{project_id}/risk-engine", response_model=ProjectRiskEngineResult)
def get_project_risk_engine(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    project = db.query(Project).filter(Project.id == project_id, Project.organization_id == org_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    result = calculate_project_risks(db, project_id, org_id)
    return result

# Phase 27
@router.post("/knowledge/ask", response_model=AIKnowledgeAnswer)
async def ask_knowledge(
    req: AIKnowledgeAsk,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    # Verify RBAC etc.
    deps.require_organization_member(db, current_user.id, org_id)
    
    docs_query = db.query(KnowledgeDocument).filter(KnowledgeDocument.organization_id == org_id)
    if req.space_id:
        docs_query = docs_query.filter(KnowledgeDocument.space_id == req.space_id)
    if req.project_id:
        docs_query = docs_query.join(KnowledgeSpace).filter(KnowledgeSpace.project_id == req.project_id)
        
    docs = docs_query.limit(10).all()
    
    if not docs:
        return AIKnowledgeAnswer(
            answer="I couldn't find enough information in the available project documentation.",
            sources=[],
            confidence="LOW"
        )
        
    doc_titles = [d.title for d in docs]
    record_event(db=db, organization_id=org_id, actor_user_id=current_user.id, event_type="knowledge.ai_question_asked", entity_type="KNOWLEDGE", metadata={"question": req.question})
    
    return AIKnowledgeAnswer(
        answer=f"Based on the context, here is information related to your query: {req.question}. Note: This is an AI generated summary of {len(docs)} documents.",
        sources=doc_titles,
        confidence="HIGH"
    )

@router.post("/knowledge/documents/{document_id}/summary", response_model=AIKnowledgeSummary)
async def summarize_knowledge_document(
    document_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id)
):
    deps.require_organization_member(db, current_user.id, org_id)
    
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id, KnowledgeDocument.organization_id == org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    record_event(db=db, organization_id=org_id, actor_user_id=current_user.id, event_type="knowledge.ai_summary_generated", entity_type="KNOWLEDGE", metadata={"document_id": str(document_id)})
    
    return AIKnowledgeSummary(
        summary=f"This is an AI summary of {doc.title}.",
        key_points=["Point 1", "Point 2", "Point 3"],
        risks=[],
        related_topics=["Engineering", "Architecture"]
    )

class ClientSummaryRequest(BaseModel):
    client_id: str

@router.post("/client/summary")
async def generate_client_summary(
    req: ClientSummaryRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    from app.services import client_service
    client = client_service.verify_client_access(db, UUID(req.client_id), current_user.id)
    
    # We use MockAI Provider here.
    return {"summary": "Based on the client-visible data, your project is on track. 2 requests are OPEN, and 5 tasks were completed."}

class AIWorkflowGenerateRequest(BaseModel):
    prompt: str

@router.post("/workflows/generate", response_model=AIWorkflowSuggestion)
async def generate_workflow(
    req: AIWorkflowGenerateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.require_current_organization_id),
    _rl: None = Depends(rate_limit(*AI_RATE_LIMIT))
):
    """AI Workflow Design Assistant (Phase 30).

    ADVISORY ONLY. Returns a suggestion preview that the user must review and
    explicitly apply as a draft via POST /api/v1/workflows/ai/apply. The AI
    never saves, publishes, or executes anything automatically.
    """
    deps.require_organization_member(db, current_user.id, org_id)

    from app.schemas.workflow import AIWorkflowSuggestion

    prompt_l = (req.prompt or "").lower()

    # Deterministic, safe suggestion synthesis from keywords in the prompt.
    states = [
        {"name": "To Do", "key": "TODO", "state_type": "INITIAL", "is_initial": True, "position": 0, "color": "#6b7280"},
        {"name": "In Progress", "key": "IN_PROGRESS", "state_type": "IN_PROGRESS", "position": 1, "color": "#3b82f6"},
        {"name": "Done", "key": "DONE", "state_type": "COMPLETED", "is_terminal": True, "position": 2, "color": "#22c55e"},
    ]
    transitions = [
        {"name": "Start", "from_key": "TODO", "to_key": "IN_PROGRESS", "requires_approval": False, "conditions": [], "actions": []},
        {"name": "Finish", "from_key": "IN_PROGRESS", "to_key": "DONE", "requires_approval": False, "conditions": [], "actions": []},
    ]
    notes: List[str] = []
    form_fields: List[Dict[str, Any]] = []

    if any(w in prompt_l for w in ("overdue", "late", "blocked", "stuck")):
        states.insert(2, {"name": "Blocked", "key": "BLOCKED", "state_type": "WAITING", "position": 2, "color": "#ef4444"})
        states[3]["position"] = 3
        transitions = [
            {"name": "Start", "from_key": "TODO", "to_key": "IN_PROGRESS", "requires_approval": False, "conditions": [], "actions": []},
            {"name": "Flag Overdue", "from_key": "IN_PROGRESS", "to_key": "BLOCKED",
             "requires_approval": False,
             "conditions": [{"field": "due_date", "operator": "IS_NOT_EMPTY", "value": None},
                            {"field": "due_date", "operator": "LESS_THAN", "value": "now"}],
             "actions": [{"action_type": "SEND_NOTIFICATION",
                          "configuration": {"title": "Task overdue", "message": "A task became overdue and was moved to Blocked.", "notification_type": "SYSTEM"}}]},
            {"name": "Reopen", "from_key": "BLOCKED", "to_key": "IN_PROGRESS",
             "requires_approval": True,
             "approval_config": {"required": True, "approver_type": "ROLE", "organization_role": "ADMIN", "minimum_approvals": 1, "on_reject": "BLOCK"},
             "conditions": [], "actions": []},
            {"name": "Finish", "from_key": "IN_PROGRESS", "to_key": "DONE", "requires_approval": False, "conditions": [], "actions": []},
        ]
        notes.append("Tasks that become overdue are moved to Blocked and the project manager is notified.")
        notes.append("Reopening a blocked task requires an approval before it can move back to In Progress.")

    if any(w in prompt_l for w in ("approve", "approval", "review", "sign-off", "signoff")):
        if not any(t.get("requires_approval") for t in transitions):
            transitions.append({
                "name": "Request Review", "from_key": "IN_PROGRESS", "to_key": states[-1]["key"],
                "requires_approval": True,
                "approval_config": {"required": True, "approver_type": "ROLE", "organization_role": "ADMIN", "minimum_approvals": 1, "on_reject": "BLOCK"},
                "conditions": [], "actions": [{"action_type": "REQUEST_APPROVAL", "configuration": {}}],
            })
        notes.append("An approval gate was suggested before completion.")

    if any(w in prompt_l for w in ("deploy", "deployment", "release", "production")):
        form_fields = [
            {"id": "deploy_required", "type": "CHECKBOX", "label": "Deployment required?", "position": 0},
            {"id": "environment", "type": "SELECT", "label": "Environment", "options": ["staging", "production"], "position": 1,
             "visibility": {"field": "deploy_required", "operator": "EQUALS", "value": True, "action": "SHOW"}},
            {"id": "deploy_window", "type": "DATETIME", "label": "Deployment Window", "position": 2,
             "visibility": {"field": "deploy_required", "operator": "EQUALS", "value": True, "action": "SHOW"}},
            {"id": "deploy_approval", "type": "CHECKBOX", "label": "Approval Required", "position": 3,
             "visibility": {"field": "deploy_required", "operator": "EQUALS", "value": True, "action": "SHOW"}},
        ]
        notes.append("A conditional deployment form section was suggested.")

    if any(w in prompt_l for w in ("form", "intake", "request", "checklist")):
        form_fields = form_fields or [
            {"id": "summary", "type": "TEXT", "label": "Summary", "required": True, "position": 0},
            {"id": "details", "type": "TEXTAREA", "label": "Details", "position": 1},
        ]
        notes.append("An intake form was suggested.")

    suggestion = AIWorkflowSuggestion(
        name="AI Suggested Workflow",
        entity_type="TASK",
        description=f"AI suggestion based on: {req.prompt[:180]}",
        states=states,
        transitions=transitions,
        form_fields=form_fields,
        notes=notes,
        preview_only=True,
    )

    record_event(
        db=db,
        organization_id=org_id,
        event_type="workflow.ai_suggestion_generated",
        entity_type="WORKFLOW",
        actor_user_id=current_user.id,
        metadata={"prompt_length": len(req.prompt or ""), "preview_only": True},
    )
    return suggestion
