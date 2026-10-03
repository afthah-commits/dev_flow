from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID
import json

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.ai_conversation import AIConversation, AIMessage
from app.schemas.ai import (
    AIConversationCreate, AIConversationResponse, AIChatRequest, AIMessageResponse,
    AIActionResponse, TaskSuggestion, TaskBreakdown, AITaskDescriptionRequest, AITaskBreakdownRequest
)
from app.services.ai.service import get_ai_provider, SYSTEM_PROMPT
from app.services.ai.context import build_project_context

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
    request: AIChatRequest
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
    org_id: UUID = Depends(deps.get_current_organization_id),
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
    org_id: UUID = Depends(deps.get_current_organization_id),
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
    org_id: UUID = Depends(deps.get_current_organization_id),
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
    current_user: User = Depends(deps.get_current_user)
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
