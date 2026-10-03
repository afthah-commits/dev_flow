from fastapi.testclient import TestClient
from app.models.project import ProjectStatus, ProjectPriority
from app.api.deps import get_db

def test_create_project(client: TestClient):
    # register and login
    client.post("/api/v1/auth/register", json={"name": "P1", "email": "p1@example.com", "password": "pass"})
    res = client.post("/api/v1/auth/login", json={"email": "p1@example.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers)
    if org_res.status_code == 201:
        headers["X-Organization-Id"] = org_res.json()["id"]

    res = client.post(
        "/api/v1/projects",
        json={
            "name": "My Project",
            "description": "Test description",
            "status": "Active",
            "priority": "High",
            "tech_stack": ["React", "Python"]
        },
        headers=headers
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "My Project"
    assert data["slug"] == "my-project"
    assert data["status"] == "Active"
    assert data["tech_stack"] == ["React", "Python"]

def test_list_projects(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "P2", "email": "p2@example.com", "password": "pass"})
    res = client.post("/api/v1/auth/login", json={"email": "p2@example.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers)
    if org_res.status_code == 201:
        headers["X-Organization-Id"] = org_res.json()["id"]

    client.post("/api/v1/projects", json={"name": "Alpha"}, headers=headers)
    client.post("/api/v1/projects", json={"name": "Beta"}, headers=headers)

    res = client.get("/api/v1/projects?sort_by=name&sort_order=asc", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["items"][0]["name"] == "Alpha"

def test_update_project(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "P3", "email": "p3@example.com", "password": "pass"})
    res = client.post("/api/v1/auth/login", json={"email": "p3@example.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers)
    if org_res.status_code == 201:
        headers["X-Organization-Id"] = org_res.json()["id"]

    create_res = client.post("/api/v1/projects", json={"name": "To Update"}, headers=headers)
    pid = create_res.json()["id"]

    patch_res = client.patch(f"/api/v1/projects/{pid}", json={"name": "Updated", "status": "Completed"}, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Updated"
    assert patch_res.json()["status"] == "Completed"

def test_security_cross_tenant(client: TestClient):
    # user A
    client.post("/api/v1/auth/register", json={"name": "U1", "email": "u1@test.com", "password": "pass"})
    resA = client.post("/api/v1/auth/login", json={"email": "u1@test.com", "password": "pass"})
    headersA = {"Authorization": f"Bearer {resA.json()['access_token']}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headersA)
    if org_res.status_code == 201:
        headersA["X-Organization-Id"] = org_res.json()["id"]
    
    p = client.post("/api/v1/projects", json={"name": "Secret Project"}, headers=headersA)
    pid = p.json()["id"]

    # user B
    client.post("/api/v1/auth/register", json={"name": "U2", "email": "u2@test.com", "password": "pass"})
    resB = client.post("/api/v1/auth/login", json={"email": "u2@test.com", "password": "pass"})
    headersB = {"Authorization": f"Bearer {resB.json()['access_token']}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headersB)
    if org_res.status_code == 201:
        headersB["X-Organization-Id"] = org_res.json()["id"]

    # B tries to get A's project
    get_res = client.get(f"/api/v1/projects/{pid}", headers=headersB)
    assert get_res.status_code in [403, 404]

    # B tries to delete A's project
    del_res = client.delete(f"/api/v1/projects/{pid}", headers=headersB)
    assert del_res.status_code in [403, 404]
