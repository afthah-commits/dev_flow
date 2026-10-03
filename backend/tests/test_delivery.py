def test_delivery_flow(client):
    """Full Phase 13 integration test: releases, deployments, pipelines, environments."""
    # 1. Register and Login
    client.post("/api/v1/auth/register", json={"name": "Release User", "email": "release@example.com", "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": "release@example.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Org
    org = client.post("/api/v1/organizations", json={"name": "Release Org", "slug": "release-org"}, headers=headers).json()
    org_id = org["id"]
    headers["X-Organization-Id"] = org_id

    # 3. Create Project
    project = client.post("/api/v1/projects", json={"name": "Release Project", "organization_id": org_id}, headers=headers).json()
    project_id = project["id"]

    # 4. Create a Task (for release mapping)
    task = client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Test Task", "status": "TODO"}, headers=headers).json()
    task_id = task["id"]

    # =========================
    # RELEASES
    # =========================

    # 5. Create Release
    res = client.post(f"/api/v1/projects/{project_id}/releases", json={
        "name": "First Release",
        "version": "v1.0.0",
        "description": "Initial release",
        "release_type": "MAJOR",
        "target_commit_sha": "abc123"
    }, headers=headers)
    assert res.status_code == 201, res.text
    release = res.json()
    release_id = release["id"]
    assert release["version"] == "v1.0.0"
    assert release["status"] == "DRAFT"

    # 6. Duplicate version fails
    res = client.post(f"/api/v1/projects/{project_id}/releases", json={
        "name": "Dup", "version": "v1.0.0"
    }, headers=headers)
    assert res.status_code == 400

    # 7. List releases
    res = client.get(f"/api/v1/projects/{project_id}/releases", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 8. Get release
    res = client.get(f"/api/v1/projects/{project_id}/releases/{release_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["version"] == "v1.0.0"

    # 9. Update release
    res = client.patch(f"/api/v1/projects/{project_id}/releases/{release_id}", json={"name": "Updated Release"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Release"

    # =========================
    # RELEASE LIFECYCLE
    # =========================

    # 10. Plan
    res = client.post(f"/api/v1/releases/{release_id}/plan", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "PLANNED"

    # 11. Invalid transition: plan again
    res = client.post(f"/api/v1/releases/{release_id}/plan", headers=headers)
    assert res.status_code == 400

    # 12. Ready
    res = client.post(f"/api/v1/releases/{release_id}/ready", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "READY"

    # 13. Release
    res = client.post(f"/api/v1/releases/{release_id}/release", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "RELEASED"
    assert res.json()["released_at"] is not None

    # =========================
    # RELEASE ITEMS
    # =========================

    # 14. Add task to release
    res = client.post(f"/api/v1/releases/{release_id}/tasks/{task_id}", headers=headers)
    assert res.status_code == 200

    # 15. List release tasks
    res = client.get(f"/api/v1/releases/{release_id}/tasks", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 16. Add PR
    res = client.post(f"/api/v1/releases/{release_id}/prs", json={"pr_number": 42, "pr_title": "Fix bug", "pr_url": "https://github.com/test/pr/42"}, headers=headers)
    assert res.status_code == 200

    # 17. List PRs
    res = client.get(f"/api/v1/releases/{release_id}/prs", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["pr_number"] == 42

    # =========================
    # ENVIRONMENTS
    # =========================

    # 18. Create environment
    res = client.post(f"/api/v1/projects/{project_id}/environments", json={
        "name": "staging", "url": "https://staging.example.com", "branch": "main"
    }, headers=headers)
    assert res.status_code == 201, res.text
    env = res.json()
    env_id = env["id"]

    # 19. Duplicate env name
    res = client.post(f"/api/v1/projects/{project_id}/environments", json={"name": "staging"}, headers=headers)
    assert res.status_code == 400

    # 20. List envs
    res = client.get(f"/api/v1/projects/{project_id}/environments", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 21. Update env
    res = client.patch(f"/api/v1/projects/{project_id}/environments/{env_id}", json={"url": "https://staging2.example.com"}, headers=headers)
    assert res.status_code == 200

    # =========================
    # DEPLOYMENTS
    # =========================

    # 22. Deploy release
    res = client.post(f"/api/v1/releases/{release_id}/deploy", json={
        "environment_id": env_id, "provider": "MOCK"
    }, headers=headers)
    assert res.status_code == 200, res.text
    dep = res.json()
    dep_id = dep["id"]
    assert dep["status"] == "SUCCESS"
    assert dep["duration_seconds"] > 0

    # 23. List deployments
    res = client.get(f"/api/v1/projects/{project_id}/deployments", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 24. Get deployment
    res = client.get(f"/api/v1/deployments/{dep_id}", headers=headers)
    assert res.status_code == 200

    # 25. Rollback
    res = client.post(f"/api/v1/deployments/{dep_id}/rollback", headers=headers)
    assert res.status_code == 200
    rb = res.json()
    assert rb["previous_deployment_id"] == dep_id

    # =========================
    # PIPELINES
    # =========================

    # 26. Run pipeline
    res = client.post(f"/api/v1/projects/{project_id}/pipelines/run", json={
        "provider": "MOCK", "branch": "main", "commit_sha": "abc123", "workflow_name": "CI"
    }, headers=headers)
    assert res.status_code == 200, res.text
    pipe = res.json()
    assert pipe["status"] == "SUCCESS"
    assert pipe["workflow_name"] == "CI"

    # 27. List pipelines
    res = client.get(f"/api/v1/projects/{project_id}/pipelines", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # =========================
    # READINESS
    # =========================

    # 28. Get readiness
    res = client.get(f"/api/v1/releases/{release_id}/readiness", headers=headers)
    assert res.status_code == 200
    readiness = res.json()
    assert "score" in readiness
    assert "explanations" in readiness

    # =========================
    # RELEASE NOTES
    # =========================

    # 29. Get notes
    res = client.get(f"/api/v1/releases/{release_id}/notes", headers=headers)
    assert res.status_code == 200

    # 30. Update notes
    res = client.patch(f"/api/v1/releases/{release_id}/notes", json={"notes": "## v1.0.0\n\nRelease notes here"}, headers=headers)
    assert res.status_code == 200

    # =========================
    # AI RELEASE NOTES
    # =========================

    # 31. Generate AI notes
    res = client.post(f"/api/v1/ai/projects/{project_id}/releases/{release_id}/generate-notes", headers=headers)
    assert res.status_code == 200
    assert "generated_notes" in res.json()
    assert res.json()["advisory"] is True

    # =========================
    # DELIVERY METRICS
    # =========================

    # 32. Delivery metrics
    res = client.get(f"/api/v1/analytics/delivery", headers=headers)
    assert res.status_code == 200
    metrics = res.json()
    assert "deployment_frequency" in metrics
    assert "pipeline_success_rate" in metrics

    # 33. DORA metrics
    res = client.get(f"/api/v1/analytics/dora", headers=headers)
    assert res.status_code == 200

    # =========================
    # CANCEL RELEASE
    # =========================

    # 34. Create another release and cancel it
    res = client.post(f"/api/v1/projects/{project_id}/releases", json={"name": "Cancel Test", "version": "v2.0.0"}, headers=headers)
    assert res.status_code == 201
    r2_id = res.json()["id"]
    res = client.post(f"/api/v1/releases/{r2_id}/cancel", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "CANCELLED"

    # =========================
    # DELETE
    # =========================

    # 35. Delete environment
    res = client.delete(f"/api/v1/projects/{project_id}/environments/{env_id}", headers=headers)
    assert res.status_code == 204

    # 36. Delete release
    res = client.delete(f"/api/v1/projects/{project_id}/releases/{r2_id}", headers=headers)
    assert res.status_code == 204
