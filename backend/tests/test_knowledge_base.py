import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project

@pytest.fixture
def auth_setup(client: TestClient, db: Session):
    email = f"user_{uuid4()}@test.com"
    client.post("/api/v1/auth/register", json={"name": "User", "email": email, "password": "pwd"})
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "pwd"})
    token = res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/api/v1/organizations", json={"name": "O1", "slug": f"o-{uuid4()}"}, headers=headers)
    org_id = res.json()["id"]
    headers["X-Organization-Id"] = org_id
    
    user = db.query(User).filter(User.email == email).first()
    return {"headers": headers, "user_id": user.id, "org_id": org_id}

def test_knowledge_space_crud(client: TestClient, db: Session, auth_setup: dict):
    headers = auth_setup["headers"]
    
    res = client.post("/api/v1/knowledge/spaces", json={
        "name": "Eng Space",
        "description": "Eng docs"
    }, headers=headers)
    assert res.status_code == 200
    space_id = res.json()["id"]
    
    res = client.get("/api/v1/knowledge/spaces", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1
    
    res = client.delete(f"/api/v1/knowledge/spaces/{space_id}", headers=headers)
    assert res.status_code == 200

def test_knowledge_document_crud(client: TestClient, db: Session, auth_setup: dict):
    headers = auth_setup["headers"]
    
    res = client.post("/api/v1/knowledge/spaces", json={"name": "Doc Space"}, headers=headers)
    space_id = res.json()["id"]
    
    res = client.post("/api/v1/knowledge/documents", json={
        "title": "Architecture 101",
        "space_id": space_id,
        "content": "# Arch"
    }, headers=headers)
    assert res.status_code == 200
    doc_id = res.json()["id"]
    
    res = client.patch(f"/api/v1/knowledge/documents/{doc_id}", json={
        "title": "Architecture 102",
        "content": "# Updated",
        "change_summary": "Updated title and content"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Architecture 102"
    
    res = client.get("/api/v1/knowledge/documents", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_knowledge_document_hierarchy_and_circular(client: TestClient, db: Session, auth_setup: dict):
    headers = auth_setup["headers"]
    
    space_res = client.post("/api/v1/knowledge/spaces", json={"name": "Tree"}, headers=headers)
    space_id = space_res.json()["id"]
    
    doc1 = client.post("/api/v1/knowledge/documents", json={"title": "Root", "space_id": space_id}, headers=headers).json()
    doc2 = client.post("/api/v1/knowledge/documents", json={"title": "Child", "space_id": space_id, "parent_id": doc1["id"]}, headers=headers).json()
    doc3 = client.post("/api/v1/knowledge/documents", json={"title": "Grandchild", "space_id": space_id, "parent_id": doc2["id"]}, headers=headers).json()
    
    res = client.patch(f"/api/v1/knowledge/documents/{doc1['id']}", json={"parent_id": doc3["id"]}, headers=headers)
    assert res.status_code == 400
    assert "Circular dependency" in res.json()["detail"]

def test_organization_isolation(client: TestClient, db: Session, auth_setup: dict):
    headers = auth_setup["headers"]
    
    org2 = Organization(id=uuid4(), name="Org 2", slug="org2", created_by=auth_setup["user_id"])
    db.add(org2)
    db.commit()
    
    res = client.get("/api/v1/search?q=test", headers=headers)
    assert res.status_code == 200
    
    res = client.post("/api/v1/ai/knowledge/ask", json={"question": "test"}, headers=headers)
    assert res.status_code == 200
