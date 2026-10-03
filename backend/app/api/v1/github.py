from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.github import GitHubConnection, ProjectGitHubRepository
from app.schemas.github import (
    GitHubStatusResponse, GitHubConnectRequest, GitHubRepositoryResponse,
    GitHubRepositoryListResponse, GitHubBranchResponse, GitHubCommitResponse,
    GitHubPullRequestResponse, GitHubIssueResponse, GitHubConnectionResponse,
    ConnectRepoRequest
)
from app.services.github_service import (
    GitHubService, encrypt_token, decrypt_token, exchange_code_for_token
)
from app.core.config import settings

router = APIRouter()

@router.get("/status", response_model=GitHubStatusResponse)
def get_status(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if conn:
        return GitHubStatusResponse(
            connected=True,
            github_username=conn.github_username,
            github_avatar_url=conn.github_avatar_url
        )
    return GitHubStatusResponse(connected=False)

@router.post("/connect")
async def connect_github(
    *,
    db: Session = Depends(deps.get_db),
    request: GitHubConnectRequest,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    try:
        # Exchange code
        access_token = await exchange_code_for_token(request.code)
        
        # Get user profile
        gh = GitHubService(access_token)
        profile = await gh.get_user_profile()
        
        # Save connection
        conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
        if not conn:
            conn = GitHubConnection(user_id=current_user.id)
            db.add(conn)
            
        conn.github_user_id = str(profile["id"])
        conn.github_username = profile["login"]
        conn.github_avatar_url = profile.get("avatar_url")
        conn.access_token_encrypted = encrypt_token(access_token)
        
        db.commit()
        return {"message": "Successfully connected to GitHub"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/disconnect")
def disconnect_github(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == current_user.id).first()
    if not conn:
        raise HTTPException(status_code=400, detail="Not connected to GitHub")
        
    db.delete(conn)
    db.commit()
    return {"message": "Successfully disconnected from GitHub"}

def get_gh_service(db: Session, user_id: UUID) -> GitHubService:
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == user_id).first()
    if not conn:
        raise HTTPException(status_code=400, detail="GitHub not connected")
    token = decrypt_token(conn.access_token_encrypted)
    return GitHubService(token)

@router.get("/repositories", response_model=GitHubRepositoryListResponse)
async def list_repositories(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1)
) -> Any:
    gh = get_gh_service(db, current_user.id)
    repos = await gh.get_repositories(page=page)
    
    items = []
    for r in repos:
        items.append(GitHubRepositoryResponse(
            id=r["id"],
            name=r["name"],
            full_name=r["full_name"],
            owner=r["owner"]["login"],
            html_url=r["html_url"],
            description=r["description"],
            default_branch=r["default_branch"],
            private=r["private"]
        ))
        
    return GitHubRepositoryListResponse(
        items=items,
        total=len(items), # GitHub API doesn't easily give total count without parsing Link header, so we just return length of page for now
        page=page
    )

# --- Project Specific Routes ---

def get_project_auth(db: Session, project_id: UUID, user_id: UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deps.require_organization_member(db, user_id, project.organization_id)
    return project

@router.get("/projects/{project_id}/github", response_model=GitHubConnectionResponse)
def get_project_repo(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    get_project_auth(db, project_id, current_user.id)
    repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not connected")
    return repo

@router.post("/projects/{project_id}/github", response_model=GitHubConnectionResponse)
async def connect_project_repo(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    request: ConnectRepoRequest,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    get_project_auth(db, project_id, current_user.id)
    
    # Verify github connection
    gh = get_gh_service(db, current_user.id)
    
    # Fetch repo details from github
    try:
        repo_data = await gh.get_repository(request.repo_full_name)
    except HTTPException:
        raise HTTPException(status_code=400, detail="Cannot access repository. Ensure it exists and you have access.")
    
    repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if not repo:
        repo = ProjectGitHubRepository(project_id=project_id)
        db.add(repo)
        
    repo.github_repository_id = str(repo_data["id"])
    repo.github_owner = repo_data["owner"]["login"]
    repo.github_name = repo_data["name"]
    repo.github_full_name = repo_data["full_name"]
    repo.github_url = repo_data["html_url"]
    repo.default_branch = repo_data["default_branch"]
    repo.private = repo_data["private"]
    repo.description = repo_data["description"]
    
    db.commit()
    db.refresh(repo)
    return repo

@router.delete("/projects/{project_id}/github")
def disconnect_project_repo(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    get_project_auth(db, project_id, current_user.id)
    repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not connected")
        
    db.delete(repo)
    db.commit()
    return {"message": "Repository disconnected"}

@router.get("/projects/{project_id}/github/branches", response_model=List[GitHubBranchResponse])
async def list_branches(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    get_project_auth(db, project_id, current_user.id)
    repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not connected")
        
    gh = get_gh_service(db, current_user.id)
    branches = await gh.get_branches(repo.github_full_name)
    
    return [GitHubBranchResponse(
        name=b["name"],
        commit_sha=b["commit"]["sha"],
        protected=b.get("protected", False)
    ) for b in branches]

@router.get("/projects/{project_id}/github/commits", response_model=List[GitHubCommitResponse])
async def list_commits(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    get_project_auth(db, project_id, current_user.id)
    repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not connected")
        
    gh = get_gh_service(db, current_user.id)
    commits = await gh.get_commits(repo.github_full_name)
    
    return [GitHubCommitResponse(
        sha=c["sha"][:7],
        message=c["commit"]["message"].split('\n')[0],
        author_name=c["commit"]["author"]["name"],
        author_avatar=c["author"]["avatar_url"] if c.get("author") else None,
        date=c["commit"]["author"]["date"],
        html_url=c["html_url"]
    ) for c in commits]

@router.get("/projects/{project_id}/github/pulls", response_model=List[GitHubPullRequestResponse])
async def list_pulls(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    state: str = Query("all")
) -> Any:
    get_project_auth(db, project_id, current_user.id)
    repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not connected")
        
    gh = get_gh_service(db, current_user.id)
    pulls = await gh.get_pull_requests(repo.github_full_name, state=state)
    
    return [GitHubPullRequestResponse(
        number=p["number"],
        title=p["title"],
        state=p["state"],
        author=p["user"]["login"],
        created_at=p["created_at"],
        updated_at=p["updated_at"],
        html_url=p["html_url"]
    ) for p in pulls]

@router.get("/projects/{project_id}/github/issues", response_model=List[GitHubIssueResponse])
async def list_issues(
    *,
    db: Session = Depends(deps.get_db),
    project_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    state: str = Query("all")
) -> Any:
    get_project_auth(db, project_id, current_user.id)
    repo = db.query(ProjectGitHubRepository).filter(ProjectGitHubRepository.project_id == project_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not connected")
        
    gh = get_gh_service(db, current_user.id)
    issues = await gh.get_issues(repo.github_full_name, state=state)
    
    return [GitHubIssueResponse(
        number=i["number"],
        title=i["title"],
        state=i["state"],
        author=i["user"]["login"],
        created_at=i["created_at"],
        updated_at=i["updated_at"],
        html_url=i["html_url"],
        labels=[l["name"] for l in i.get("labels", [])]
    ) for i in issues]
