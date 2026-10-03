export interface GitHubStatus {
  connected: boolean;
  github_username?: string;
  github_avatar_url?: string;
}

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  owner: string;
  html_url: string;
  description?: string;
  default_branch: string;
  private: boolean;
}

export interface GitHubRepositoryListResponse {
  items: GitHubRepository[];
  total: number;
  page: number;
}

export interface GitHubBranch {
  name: string;
  commit_sha: string;
  protected: boolean;
}

export interface GitHubCommit {
  sha: string;
  message: string;
  author_name: string;
  author_avatar?: string;
  date: string;
  html_url: string;
}

export interface GitHubPullRequest {
  number: number;
  title: string;
  state: string;
  author: string;
  created_at: string;
  updated_at: string;
  html_url: string;
}

export interface GitHubIssue {
  number: number;
  title: string;
  state: string;
  author: string;
  created_at: string;
  updated_at: string;
  html_url: string;
  labels: string[];
}

export interface GitHubConnectionResponse {
  project_id: string;
  github_repository_id: string;
  github_full_name: string;
  github_url: string;
  connected_at: string;
}
