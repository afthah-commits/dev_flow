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

@pytest.fixture(autouse=True)
def _isolate_auth_overrides():
    """Register this module's auth overrides for its own tests only.

    Previously these were assigned at import time (i.e. during collection), so
    they leaked into every test collected afterwards and silently bypassed
    authentication for the rest of the suite.
    """
    app.dependency_overrides[deps.get_current_user] = override_get_current_user
    app.dependency_overrides[deps.get_current_organization_id] = override_get_current_organization_id
    yield
    app.dependency_overrides.pop(deps.get_current_user, None)
    app.dependency_overrides.pop(deps.get_current_organization_id, None)

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

def test_analytics_query_trend(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.v1.analytics.check_permission", lambda *args, **kwargs: None)
    response = client.post(
        "/api/v1/analytics/query",
        json={"metric": "tasks.completed", "group_by": "date"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "tasks.completed"
    assert isinstance(data["data"], list)

def test_analytics_export_success(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.v1.analytics.check_permission", lambda *args, **kwargs: None)
    response = client.post(
        "/api/v1/analytics/export?format=csv",
        json={"metric": "sprint.velocity"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"
    assert isinstance(data["data"], list)
