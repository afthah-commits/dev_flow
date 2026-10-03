from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, timedelta

def test_analytics_and_notifications(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "A", "email": "a@example.com", "password": "pass"})
    res = client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers)
    if org_res.status_code == 201:
        headers["X-Organization-Id"] = org_res.json()["id"]
    
    # Dashboard empty
    dash = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert dash.status_code == 200
    assert dash.json()["total_projects"] == 0

    # Project and Tasks
    p = client.post("/api/v1/projects", json={"name": "Pro"}, headers=headers)
    pid = p.json()["id"]

    now = datetime.now(timezone.utc)
    overdue_date = (now - timedelta(days=2)).isoformat()
    future_date = (now + timedelta(days=2)).isoformat()
    
    # 1 Done task
    client.post(f"/api/v1/projects/{pid}/tasks", json={"title": "Done", "status": "DONE", "priority": "HIGH"}, headers=headers)
    # 1 Overdue Task
    client.post(f"/api/v1/projects/{pid}/tasks", json={"title": "Overdue", "status": "TODO", "priority": "CRITICAL", "due_date": overdue_date}, headers=headers)
    # 1 Future task
    client.post(f"/api/v1/projects/{pid}/tasks", json={"title": "Future", "status": "IN_PROGRESS", "priority": "LOW", "due_date": future_date}, headers=headers)

    # Analytics Project
    pa = client.get(f"/api/v1/analytics/projects/{pid}", headers=headers)
    assert pa.status_code == 200
    data = pa.json()
    assert data["total_tasks"] == 3
    assert data["completed"] == 1
    assert data["overdue"] == 1
    assert data["deadlines"]["overdue"] == 1
    assert data["deadlines"]["due_soon"] == 1
    
    # Health should be calculated based on factors
    assert data["health"]["status"] in ["Healthy", "Attention", "At Risk"]

    # Notifications check
    nots = client.get("/api/v1/notifications", headers=headers)
    assert nots.status_code == 200
    
    count = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count.json()["count"] > 0
    
    # Preferences
    prefs = client.get("/api/v1/notifications/preferences", headers=headers)
    assert prefs.status_code == 200
    
    client.patch("/api/v1/notifications/preferences", json={
        "task_notifications": False, "deadline_notifications": False, "project_health_notifications": False,
        "github_notifications": False, "ai_notifications": False
    }, headers=headers)
    
    # Mark read
    client.patch("/api/v1/notifications/read-all", headers=headers)
    count2 = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count2.json()["count"] == 0

    # Cross user security
    client.post("/api/v1/auth/register", json={"name": "B", "email": "b@example.com", "password": "pass"})
    res2 = client.post("/api/v1/auth/login", json={"email": "b@example.com", "password": "pass"})
    headers2 = {"Authorization": f"Bearer {res2.json()['access_token']}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers2)
    if org_res.status_code == 201:
        headers2["X-Organization-Id"] = org_res.json()["id"]
    
    err = client.get(f"/api/v1/analytics/projects/{pid}", headers=headers2)
    assert err.status_code in [403, 404]
