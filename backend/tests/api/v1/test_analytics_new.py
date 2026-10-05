import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.api import deps
import uuid
from app.models.user import User

class MockUser:
    id = str(uuid.uuid4())
    email = "test@example.com"
    is_active = True
    is_superuser = False

def override_get_current_user():
    return MockUser()

def override_get_current_organization_id():
    return uuid.uuid4()

app.dependency_overrides[deps.get_current_user] = override_get_current_user
app.dependency_overrides[deps.get_current_organization_id] = override_get_current_organization_id

def test_executive_analytics_success(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.v1.analytics.check_permission", lambda *args, **kwargs: None)
    
    response = client.get(
        "/api/v1/analytics/executive"
    )
    assert response.status_code == 200
    data = response.json()
    assert "active_projects" in data
    assert "failed_deployments" in data
    
def test_project_analytics_not_found(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.v1.analytics.check_permission", lambda *args, **kwargs: None)
    response = client.get(
        f"/api/v1/analytics/projects/{uuid.uuid4()}"
    )
    assert response.status_code == 404

def test_analytics_query_unauthorized_metric(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.v1.analytics.check_permission", lambda *args, **kwargs: None)
    response = client.post(
        "/api/v1/analytics/query",
        json={"metric": "unknown.metric"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown metric"

def test_analytics_query_success(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.v1.analytics.check_permission", lambda *args, **kwargs: None)
    response = client.post(
        "/api/v1/analytics/query",
        json={"metric": "tasks.completed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "tasks.completed"
    assert "data" in data
