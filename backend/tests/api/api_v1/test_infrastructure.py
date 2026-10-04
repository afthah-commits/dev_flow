def test_infrastructure_flow(client):
    # 1. Register and Login
    client.post("/api/v1/auth/register", json={"name": "Infra User", "email": "infra@example.com", "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": "infra@example.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Org
    org = client.post("/api/v1/organizations", json={"name": "Infra Org", "slug": "infra-org"}, headers=headers).json()
    org_id = org["id"]
    headers["X-Organization-Id"] = org_id

    # 3. Create Project
    project = client.post("/api/v1/projects", json={"name": "Infra Project", "organization_id": org_id}, headers=headers).json()
    project_id = project["id"]

    # 4. Create Environment
    env = client.post(
        f"/api/v1/projects/{project_id}/environments",
        json={"name": "Prod Env", "environment_type": "PRODUCTION", "status": "ACTIVE"},
        headers=headers
    ).json()
    env_id = env["id"]

    # 5. Env Health & Variables
    h1 = client.get(f"/api/v1/environments/{env_id}/health", headers=headers)
    assert h1.status_code == 200

    h2 = client.post(f"/api/v1/environments/{env_id}/health/check", headers=headers)
    assert h2.status_code == 200

    v1 = client.post(
        f"/api/v1/environments/{env_id}/variables",
        headers=headers,
        json={"key": "SECRET", "value": "password", "is_secret": True}
    )
    assert v1.status_code == 200
    var_id = v1.json()["id"]

    v2 = client.get(f"/api/v1/environments/{env_id}/variables", headers=headers)
    assert v2.status_code == 200

    v3 = client.patch(
        f"/api/v1/environments/{env_id}/variables/{var_id}",
        headers=headers,
        json={"value": "newpass"}
    )
    assert v3.status_code == 200

    v4 = client.delete(f"/api/v1/environments/{env_id}/variables/{var_id}", headers=headers)
    assert v4.status_code == 200

    # 6. Deployment Rollback & Approvals
    # First create a release and deployment
    rel = client.post(
        f"/api/v1/projects/{project_id}/releases",
        headers=headers,
        json={"name": "v1.0", "version": "1.0", "description": "Release"}
    ).json()
    release_id = rel["id"]
    dep = client.post(
        f"/api/v1/releases/{release_id}/deploy",
        headers=headers,
        json={"environment_id": env_id, "provider": "MOCK"}
    ).json()
    dep_id = dep["id"]

    a1 = client.post(
        f"/api/v1/deployments/{dep_id}/approvals",
        headers=headers,
        json={"deployment_id": dep_id, "status": "APPROVED", "comment": "looks good"}
    )
    assert a1.status_code == 200

    r1 = client.post(
        f"/api/v1/deployments/{dep_id}/rollback",
        headers=headers
    )
    assert r1.status_code == 200

    # 7. Deployment Incidents
    inc = client.post(
        f"/api/v1/deployment_incidents",
        headers=headers,
        json={"environment_id": env_id, "severity": "HIGH", "title": "DB Down"}
    )
    assert inc.status_code == 200
    inc_id = inc.json()["id"]

    inc_get = client.get(f"/api/v1/deployment_incidents/{inc_id}", headers=headers)
    assert inc_get.status_code == 200

    inc_up = client.patch(
        f"/api/v1/deployment_incidents/{inc_id}",
        headers=headers,
        json={"status": "RESOLVED"}
    )
    assert inc_up.status_code == 200

    # 8. Analytics
    analytics = client.get(f"/api/v1/infrastructure/analytics?organization_id={org_id}", headers=headers)
    assert analytics.status_code == 200
