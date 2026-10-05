import pytest
from fastapi.testclient import TestClient

def test_phase32_readiness(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "P32 User", "email": "p32@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "p32@example.com", "password": "password123"}).json()
    token = login_res["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    my_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]

    org = client.post("/api/v1/organizations", json={"name": "P32 Org", "slug": "p32-org"}, headers=headers).json()
    org_id = org["id"]
    headers["X-Organization-Id"] = org_id

    res = client.post("/api/v1/projects", headers=headers, json={
        "name": "Phase 32 Proj",
        "key": "P32",
        "description": "Test proj"
    })
    proj_id = res.json()["id"]

    res = client.post(f"/api/v1/projects/{proj_id}/releases", headers=headers, json={
        "name": "Rel 1",
        "version": "v1.0.0",
        "release_type": "MAJOR",
        "description": "This is a detailed description for the release.",
        "target_environment": "Production"
    })
    release_id = res.json()["id"]

    # check readiness
    res = client.get(f"/api/v1/releases/{release_id}/readiness", headers=headers)
    data = res.json()
    assert "ready" in data
    assert "score" in data
    assert "checks" in data
    assert data["ready"] is True  # draft with no tasks is technically ready because it has nothing

    # request approval
    res = client.post(f"/api/v1/releases/{release_id}/approvals", headers=headers, json={
        "reviewer_id": my_id,
        "comment": "Pls approve"
    })
    assert res.status_code == 200
    approval_id = res.json()["id"]

    # approve
    res = client.post(f"/api/v1/releases/approvals/{approval_id}/approve", headers=headers)
    assert res.status_code == 200
    
    # check release status
    res = client.get(f"/api/v1/projects/{proj_id}/releases/{release_id}", headers=headers)
    assert res.json()["status"] == "APPROVED"
    
    # mock deploy
    res = client.post(f"/api/v1/releases/{release_id}/deploy", headers=headers, json={
        "provider": "MOCK"
    })
    assert res.status_code == 200
    
    # check status again
    res = client.get(f"/api/v1/projects/{proj_id}/releases/{release_id}", headers=headers)
    assert res.json()["status"] == "DEPLOYED"

    # promote
    res = client.post(f"/api/v1/releases/{release_id}/promote?target_env=Production", headers=headers)
    assert res.status_code == 200
    assert res.json()["target_environment"] == "Production"

    # rollback
    res = client.post(f"/api/v1/releases/{release_id}/rollback", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "ROLLED_BACK"
