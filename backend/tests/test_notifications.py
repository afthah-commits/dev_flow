def test_notifications_flow(client):
    # 1. Register and Login
    client.post("/api/v1/auth/register", json={"name": "Notif User", "email": "notif@example.com", "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": "notif@example.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get unread count (should be 0)
    res = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert res.status_code == 200
    assert res.json()["count"] == 0
    
    # 3. Get preferences
    res = client.get("/api/v1/notifications/preferences", headers=headers)
    assert res.status_code == 200
    assert res.json()["task_notifications"] is True
    
    # Update preferences
    res = client.patch("/api/v1/notifications/preferences", json={
        "task_notifications": False,
        "deadline_notifications": True,
        "project_health_notifications": True,
        "github_notifications": True,
        "ai_notifications": True,
        "task_assignments": True,
        "sprint_events": True,
        "milestone_events": True,
        "security_events": True,
        "digest_notifications": False
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["task_notifications"] is False
