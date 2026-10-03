from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.task import Task
from app.api.v1.github import get_gh_service
from app.models.github import ProjectGitHubRepository
from uuid import UUID

async def build_project_context(db: Session, project_id: UUID, user_id: UUID) -> str:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return "No project context available."
        
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    context = f"PROJECT CONTEXT:\nName: {project.name}\nStatus: {project.status}\nPriority: {project.priority}\n"
    context += f"Description: {project.description or 'None'}\n"
    context += f"Tech Stack: {', '.join(project.tech_stack)}\n"
    
    total = len(tasks)
    done = len([t for t in tasks if t.status == 'DONE'])
    in_progress = len([t for t in tasks if t.status == 'IN_PROGRESS'])
    
    context += f"Tasks: {total} total, {in_progress} in progress, {done} completed.\n\n"
    
    # Try to add GH context
    gh_repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if gh_repo:
        context += f"GITHUB CONTEXT:\nRepository: {gh_repo.github_full_name}\nDefault Branch: {gh_repo.default_branch}\n"
        try:
            gh = get_gh_service(db, user_id)
            commits = await gh.get_commits(gh_repo.github_full_name, per_page=5)
            context += "Recent Commits:\n"
            for c in commits:
                context += f"- {c['commit']['message']} by {c['commit']['author']['name']}\n"
        except Exception:
            context += "Could not fetch recent commits.\n"

    return context
