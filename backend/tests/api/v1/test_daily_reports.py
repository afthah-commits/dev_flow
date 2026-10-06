import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.api import deps
import uuid
from datetime import date
from app.models.user import User
from app.models.daily_report import DailyReport

class MockUser:
    id = uuid.uuid4()
    email = "test@example.com"
    is_active = True
    is_superuser = False

mock_user = MockUser()
mock_org_id = uuid.uuid4()

def override_get_current_user():
    return mock_user

def override_get_current_organization_id():
    return mock_org_id

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

def test_create_daily_report(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    
    response = client.post(
        "/api/v1/daily-reports/",
        json={
            "report_date": "2026-10-03",
            "completed_tasks": ["Implemented generic filtering"],
            "next_plan": ["Continue CRM mobile application development"],
            "blockers": ["None"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["report_date"] == "2026-10-03"
    assert "Implemented generic filtering" in data["completed_tasks"]
    assert "id" in data
    
    # Store ID for next tests if needed, but DB is persistent in tests sometimes, wait we'll create independent instances.

def test_duplicate_daily_report(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    
    client.post(
        "/api/v1/daily-reports/",
        json={
            "report_date": "2026-10-04",
            "completed_tasks": ["Task A"],
            "next_plan": ["Task B"],
            "blockers": ["None"]
        }
    )
    
    response = client.post(
        "/api/v1/daily-reports/",
        json={
            "report_date": "2026-10-04",
            "completed_tasks": ["Task A2"],
            "next_plan": ["Task B2"],
            "blockers": ["None"]
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_list_daily_reports(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    response = client.get("/api/v1/daily-reports/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_export_daily_report(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    
    resp_create = client.post(
        "/api/v1/daily-reports/",
        json={
            "report_date": "2026-10-05",
            "completed_tasks": ["Export task"],
            "next_plan": ["Export plan"],
            "blockers": ["Export blocker"]
        }
    )
    report_id = resp_create.json()["id"]

    response = client.post(f"/api/v1/daily-reports/{report_id}/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    content = response.content.decode()
    assert "Export task" in content
    assert "Export plan" in content
    assert "Export blocker" in content
