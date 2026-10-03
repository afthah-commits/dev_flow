def test_time_flow(client):
    # 1. Register and Login
    client.post("/api/v1/auth/register", json={"name": "Time User", "email": "time@example.com", "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": "time@example.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Org
    org = client.post("/api/v1/organizations", json={"name": "Time Org", "slug": "time-org"}, headers=headers).json()
    org_id = org["id"]
    headers["X-Organization-Id"] = org_id
    
    # 3. Create Project
    project = client.post("/api/v1/projects", json={"name": "Time Project", "organization_id": org_id}, headers=headers).json()
    project_id = project["id"]
    
    # 4. Start Timer
    res = client.post("/api/v1/time/timer/start", json={
        "project_id": project_id,
        "description": "Timer test"
    }, headers=headers)
    assert res.status_code == 200, res.text
    timer_id = res.json()["id"]
    
    # 5. Prevent Duplicate Timer
    res = client.post("/api/v1/time/timer/start", json={
        "project_id": project_id,
        "description": "Another"
    }, headers=headers)
    assert res.status_code == 400
    
    # 6. Stop Timer
    res = client.post("/api/v1/time/timer/stop", headers=headers)
    assert res.status_code == 200
    
    # 7. Create Manual Entry
    res = client.post("/api/v1/time/entries", json={
        "project_id": project_id,
        "description": "Manual entry",
        "started_at": "2026-10-01T10:00:00Z",
        "duration_seconds": 3600,
        "billable": True
    }, headers=headers)
    assert res.status_code == 201
    entry_id = res.json()["id"]
    
    # 8. List Entries
    res = client.get("/api/v1/time/entries", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 2 # 1 timer + 1 manual
    
    # 9. Edit Entry
    res = client.patch(f"/api/v1/time/entries/{entry_id}", json={
        "description": "Updated manual"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["description"] == "Updated manual"
    
    # 10. Delete Entry
    res = client.delete(f"/api/v1/time/entries/{entry_id}", headers=headers)
    assert res.status_code == 200
    
    # 11. Project Time Stats
    res = client.get(f"/api/v1/projects/{project_id}/time/stats", headers=headers)
    assert res.status_code == 200
    assert "total_tracked_hours" in res.json()
    
    # 12. Productivity Analytics
    res = client.get("/api/v1/analytics/productivity", headers=headers)
    assert res.status_code == 200
    assert "active_days" in res.json()
