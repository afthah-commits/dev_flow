import httpx
from cryptography.fernet import Fernet
from fastapi import HTTPException
from typing import Dict, Any, List
from app.core.config import settings

def _get_fernet() -> Fernet:
    if not settings.GITHUB_TOKEN_ENCRYPTION_KEY:
        raise ValueError("GITHUB_TOKEN_ENCRYPTION_KEY is missing")
    return Fernet(settings.GITHUB_TOKEN_ENCRYPTION_KEY.encode())

def encrypt_token(token: str) -> str:
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    f = _get_fernet()
    return f.decrypt(encrypted_token.encode()).decode()

class GitHubService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.base_url = "https://api.github.com"

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="GitHub token expired or revoked")
        elif response.status_code == 403:
            # Check for rate limit
            if "X-RateLimit-Remaining" in response.headers and response.headers["X-RateLimit-Remaining"] == "0":
                raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
            raise HTTPException(status_code=403, detail="GitHub access forbidden")
        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub resource not found")
        
        response.raise_for_status()
        return response.json()

    async def get_user_profile(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{self.base_url}/user", headers=self.headers)
            return self._handle_response(res)
            
    async def get_repositories(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            # We fetch user repos and also repos they have access to
            res = await client.get(
                f"{self.base_url}/user/repos", 
                params={"sort": "updated", "per_page": per_page, "page": page},
                headers=self.headers
            )
            return self._handle_response(res)
            
    async def get_repository(self, full_name: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{self.base_url}/repos/{full_name}", headers=self.headers)
            return self._handle_response(res)

    async def get_branches(self, full_name: str, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/repos/{full_name}/branches",
                params={"per_page": per_page, "page": page},
                headers=self.headers
            )
            return self._handle_response(res)

    async def get_commits(self, full_name: str, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/repos/{full_name}/commits",
                params={"per_page": per_page, "page": page},
                headers=self.headers
            )
            return self._handle_response(res)

    async def get_pull_requests(self, full_name: str, state: str = "all", page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/repos/{full_name}/pulls",
                params={"state": state, "sort": "updated", "direction": "desc", "per_page": per_page, "page": page},
                headers=self.headers
            )
            return self._handle_response(res)

    async def get_issues(self, full_name: str, state: str = "all", page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/repos/{full_name}/issues",
                params={"state": state, "sort": "updated", "direction": "desc", "per_page": per_page, "page": page},
                headers=self.headers
            )
            # GitHub API returns PRs as issues too, we filter them out
            data = self._handle_response(res)
            return [i for i in data if "pull_request" not in i]

async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI
            }
        )
        data = res.json()
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error_description"])
        return data["access_token"]
