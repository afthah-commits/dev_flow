from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class GitHubStatusResponse(BaseModel):
    connected: bool
    github_username: Optional[str] = None
    github_avatar_url: Optional[str] = None

class GitHubRepositoryResponse(BaseModel):
    id: int
    name: str
    full_name: str
    owner: str
    html_url: str
    description: Optional[str] = None
    default_branch: str
    private: bool

class GitHubRepositoryListResponse(BaseModel):
    items: List[GitHubRepositoryResponse]
    total: int
    page: int

class GitHubBranchResponse(BaseModel):
    name: str
    commit_sha: str
    protected: bool

class GitHubCommitResponse(BaseModel):
    sha: str
    message: str
    author_name: str
    author_avatar: Optional[str] = None
    date: str
    html_url: str

class GitHubPullRequestResponse(BaseModel):
    number: int
    title: str
    state: str
    author: str
    created_at: str
    updated_at: str
    html_url: str

class GitHubIssueResponse(BaseModel):
    number: int
    title: str
    state: str
    author: str
    created_at: str
    updated_at: str
    html_url: str
    labels: List[str]

class GitHubConnectionResponse(BaseModel):
    project_id: UUID
    github_repository_id: str
    github_full_name: str
    github_url: str
    connected_at: datetime

class GitHubConnectRequest(BaseModel):
    code: str
    state: str

class ConnectRepoRequest(BaseModel):
    repo_full_name: str
