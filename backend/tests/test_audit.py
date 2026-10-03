def test_audit_flow(client):
    # 1. Register and Login
    client.post("/api/v1/auth/register", json={"name": "Audit User", "email": "audit@example.com", "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": "audit@example.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Org
    org = client.post("/api/v1/organizations", json={"name": "Audit Org", "slug": "audit-org"}, headers=headers).json()
    org_id = org["id"]
    
    # 3. Create Project
    client.post("/api/v1/projects", json={"name": "Audit Project", "organization_id": org_id}, headers={**headers, "X-Organization-Id": str(org_id)}).json()
    
    # 4. Fetch Audit Logs
    res = client.get(f"/api/v1/audit/events?organization_id={org_id}", headers=headers)
    assert res.status_code == 200
    events = res.json()["items"]
    
    assert len(events) >= 1
    # Check that PROJECT_CREATED is in the events
    event_types = [e["event_type"] for e in events]
    assert "PROJECT_CREATED" in event_types
