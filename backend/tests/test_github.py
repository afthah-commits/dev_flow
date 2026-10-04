from fastapi.testclient import TestClient
from unittest.mock import patch

def test_github_auth_and_repo(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "GHUser", "email": "gh@example.com", "password": "pass"})
    res = client.post("/api/v1/auth/login", json={"email": "gh@example.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers)
    if org_res.status_code == 201:
        headers["X-Organization-Id"] = org_res.json()["id"]
    
    # 1. Not connected
    st = client.get("/api/v1/github/status", headers=headers)
    assert st.status_code == 200
    assert st.json()["connected"] is False

    # 2. Connect mock
    from unittest.mock import AsyncMock
    with patch("app.api.v1.github.exchange_code_for_token", new_callable=AsyncMock) as mock_ex:
        with patch("app.api.v1.github.GitHubService") as mock_gh:
            mock_ex.return_value = "fake_token"
            gh_inst = mock_gh.return_value
            gh_inst.get_user_profile = AsyncMock(return_value={"id": 123, "login": "testuser", "avatar_url": "url"})
            
            c = client.post("/api/v1/github/connect", json={"code": "123", "state": "abc"}, headers=headers)
            assert c.status_code == 200, c.text

    # 3. Status connected
    st2 = client.get("/api/v1/github/status", headers=headers)
    assert st2.json()["connected"] is True
    assert st2.json()["github_username"] == "testuser"
    
    # 4. Project connect mock
    p = client.post("/api/v1/projects", json={"name": "My GH Proj"}, headers=headers)
    pid = p.json()["id"]

    with patch("app.api.v1.github.GitHubService") as mock_gh:
        gh_inst = mock_gh.return_value
        gh_inst.get_repository = AsyncMock(return_value={
            "id": 999, "owner": {"login": "testuser"}, "name": "repo", "full_name": "testuser/repo",
            "html_url": "url", "default_branch": "main", "private": False, "description": "desc"
        })
        
        pr = client.post(f"/api/v1/github/projects/{pid}/github", json={"repo_full_name": "testuser/repo"}, headers=headers)
        assert pr.status_code == 200
        assert pr.json()["github_full_name"] == "testuser/repo"
        
        # Test branches
        gh_inst.get_branches = AsyncMock(return_value=[{"name": "main", "commit": {"sha": "abc"}, "protected": False}])
        b = client.get(f"/api/v1/github/projects/{pid}/github/branches", headers=headers)
        assert b.json()[0]["name"] == "main"
        
        # Test security (cross-user)
        client.post("/api/v1/auth/register", json={"name": "U2", "email": "u2@example.com", "password": "pass"})
        res2 = client.post("/api/v1/auth/login", json={"email": "u2@example.com", "password": "pass"})
        token2 = res2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        org_res2 = client.post("/api/v1/organizations", json={"name": "Test Org 2", "slug": "test-org-2"}, headers=headers2)
        if org_res2.status_code == 201:
            headers2["X-Organization-Id"] = org_res2.json()["id"]
            
        err = client.get(f"/api/v1/github/projects/{pid}/github", headers=headers2)
        assert err.status_code in [403, 404]
        
        # Disconnect repo
        d = client.delete(f"/api/v1/github/projects/{pid}/github", headers=headers)
        assert d.status_code == 200
