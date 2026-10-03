from fastapi.testclient import TestClient
from app.models.task import TaskStatus, TaskPriority

def test_task_crud(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "T1", "email": "t1@example.com", "password": "pass"})
    res = client.post("/api/v1/auth/login", json={"email": "t1@example.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headers)
    if org_res.status_code == 201:
        headers["X-Organization-Id"] = org_res.json()["id"]

    # create project
    p = client.post("/api/v1/projects", json={"name": "Project 1"}, headers=headers)
    pid = p.json()["id"]

    # create task
    t = client.post(
        f"/api/v1/projects/{pid}/tasks", 
        json={"title": "My Task", "priority": "HIGH"},
        headers=headers
    )
    assert t.status_code == 201
    tid = t.json()["id"]

    # list tasks
    l = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers)
    assert l.json()["total"] == 1
    
    # get stats
    s = client.get(f"/api/v1/projects/{pid}/tasks/stats", headers=headers)
    assert s.json()["total"] == 1
    assert s.json()["todo"] == 1

    # update status
    u = client.patch(
        f"/api/v1/projects/{pid}/tasks/{tid}/status",
        json={"status": "IN_PROGRESS"},
        headers=headers
    )
    assert u.json()["status"] == "IN_PROGRESS"

    # delete task
    d = client.delete(f"/api/v1/projects/{pid}/tasks/{tid}", headers=headers)
    assert d.status_code == 200

def test_task_security(client: TestClient):
    # user A
    client.post("/api/v1/auth/register", json={"name": "U_A", "email": "ua@example.com", "password": "pass"})
    resA = client.post("/api/v1/auth/login", json={"email": "ua@example.com", "password": "pass"})
    headersA = {"Authorization": f"Bearer {resA.json()['access_token']}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headersA)
    if org_res.status_code == 201:
        headersA["X-Organization-Id"] = org_res.json()["id"]
    
    p = client.post("/api/v1/projects", json={"name": "A Project"}, headers=headersA)
    pid = p.json()["id"]

    t = client.post(f"/api/v1/projects/{pid}/tasks", json={"title": "A Task"}, headers=headersA)
    tid = t.json()["id"]

    # user B
    client.post("/api/v1/auth/register", json={"name": "U_B", "email": "ub@example.com", "password": "pass"})
    resB = client.post("/api/v1/auth/login", json={"email": "ub@example.com", "password": "pass"})
    headersB = {"Authorization": f"Bearer {resB.json()['access_token']}"}
    org_res = client.post("/api/v1/organizations", json={"name": "Test Org"}, headers=headersB)
    if org_res.status_code == 201:
        headersB["X-Organization-Id"] = org_res.json()["id"]

    # B tries to get A's task list
    l = client.get(f"/api/v1/projects/{pid}/tasks", headers=headersB)
    assert l.status_code in [403, 404]

    # B tries to get A's task
    g = client.get(f"/api/v1/projects/{pid}/tasks/{tid}", headers=headersB)
    assert g.status_code in [403, 404]
