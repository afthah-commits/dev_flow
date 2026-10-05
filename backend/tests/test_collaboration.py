def test_collaboration_flow(client):
    # 1. Register and Login
    client.post("/api/v1/auth/register", json={"name": "Collab User", "email": "collab@example.com", "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": "collab@example.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Org and Project
    org = client.post("/api/v1/organizations", json={"name": "Collab Org", "slug": "collab-org"}, headers=headers).json()
    org_id = org["id"]
    headers["X-Organization-Id"] = org_id
    project = client.post("/api/v1/projects", json={"name": "Collab Project", "organization_id": org_id}, headers=headers).json()
    project_id = project["id"]

    # 3. Create Discussion
    disc = client.post(f"/api/v1/projects/{project_id}/discussions", json={
        "title": "Architecture Plan",
        "content": "Let's discuss the new architecture."
    }, headers=headers).json()
    disc_id = disc["id"]
    assert disc["status"] == "OPEN"

    # 4. Create Comment on Discussion
    comment = client.post("/api/v1/comments", json={
        "entity_type": "DISCUSSION",
        "entity_id": disc_id,
        "content": "I agree with the plan."
    }, headers=headers).json()
    comment_id = comment["id"]
    assert comment["content"] == "I agree with the plan."

    # 5. List Comments
    comments = client.get(f"/api/v1/comments?entity_type=DISCUSSION&entity_id={disc_id}", headers=headers).json()
    assert len(comments) == 1
    
    # 6. Reply to Comment
    reply = client.post("/api/v1/comments", json={
        "entity_type": "DISCUSSION",
        "entity_id": disc_id,
        "parent_id": comment_id,
        "content": "Me too!"
    }, headers=headers).json()
    assert reply["parent_id"] == comment_id

    # 7. Get Replies
    replies = client.get(f"/api/v1/comments/{comment_id}/replies", headers=headers).json()
    assert len(replies) == 1

    # 8. Edit Comment
    updated = client.patch(f"/api/v1/comments/{comment_id}", json={"content": "Updated comment"}, headers=headers).json()
    assert updated["content"] == "Updated comment"
    assert updated["is_edited"] is True

    # 9. React to Comment
    rxn = client.post(f"/api/v1/comments/{comment_id}/reactions", json={"reaction": "👍"}, headers=headers).json()
    assert rxn["reaction"] == "👍"

    # 10. Remove Reaction
    res = client.delete(f"/api/v1/comments/{comment_id}/reactions/👍", headers=headers)
    assert res.status_code == 204

    # 11. Pin Comment
    pinned = client.post(f"/api/v1/comments/{comment_id}/pin", headers=headers).json()
    assert pinned["is_pinned"] is True

    # 12. Search
    search = client.get(f"/api/v1/search?q=Architecture", headers=headers).json()
    assert isinstance(search, list)
    discussion_hits = [r for r in search if r.get("entity_type") == "DISCUSSION" and "Architecture" in r.get("title", "")]
    assert len(discussion_hits) >= 1

    # 13. Delete Comment
    res = client.delete(f"/api/v1/comments/{comment_id}", headers=headers)
    assert res.status_code == 204
