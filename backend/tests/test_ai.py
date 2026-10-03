from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

def test_ai_conversations(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "AIUser", "email": "ai@example.com", "password": "pass"})
    res = client.post("/api/v1/auth/login", json={"email": "ai@example.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers)
    if org_res.status_code == 201:
        headers["X-Organization-Id"] = org_res.json()["id"]
    
    # Create project
    p = client.post("/api/v1/projects", json={"name": "AI Project"}, headers=headers)
    pid = p.json()["id"]

    # Create conv
    c = client.post("/api/v1/ai/conversations", json={"title": "Test Chat", "project_id": pid}, headers=headers)
    assert c.status_code == 200
    cid = c.json()["id"]
    
    # Send message (mock AI provider will respond)
    m = client.post(f"/api/v1/ai/conversations/{cid}/messages", json={"message": "summary"}, headers=headers)
    assert m.status_code == 200
    assert "mock summary" in m.json()["content"]
    
    # Structured output test (Task suggestion)
    sg = client.post(f"/api/v1/ai/projects/{pid}/actions/task-suggestion", json={"instruction": "Add login"}, headers=headers)
    assert sg.status_code == 200
    assert sg.json()["structured_data"]["title"] == "Generated Task"

    # Cross user security
    client.post("/api/v1/auth/register", json={"name": "U2", "email": "u2ai@example.com", "password": "pass"})
    res2 = client.post("/api/v1/auth/login", json={"email": "u2ai@example.com", "password": "pass"})
    token2 = res2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers2)
    if org_res.status_code == 201:
        headers2["X-Organization-Id"] = org_res.json()["id"]

    err = client.get(f"/api/v1/ai/conversations/{cid}", headers=headers2)
    assert err.status_code == 404
