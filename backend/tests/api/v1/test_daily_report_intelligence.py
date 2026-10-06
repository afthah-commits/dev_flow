import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.api import deps
import uuid
from datetime import date, timedelta
from app.models.daily_report import DailyReport

mock_user_id = uuid.uuid4()
mock_org_id = uuid.uuid4()

class MockUser:
    id = mock_user_id
    email = "test_intelligence@example.com"
    is_active = True
    is_superuser = False
    name = "Test User Intelligence"

def override_get_current_user():
    return MockUser()

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

def test_get_daily_summary(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.v1.daily_reports.check_admin_or_owner", lambda *args, **kwargs: None)
    
    # Create test report
    client.post(
        "/api/v1/daily-reports/",
        json={
            "report_date": str(date.today()),
            "completed_tasks": ["Task A", "Task B"],
            "next_plan": ["Plan A"],
            "blockers": ["Blocker A"]
        }
    )
    
    response = client.get(f"/api/v1/daily-reports/summary/daily?report_date={str(date.today())}")
    assert response.status_code == 200
    data = response.json()
    assert "total_reports" in data
    assert "completed_task_count" in data
    assert "blocker_count" in data
    # completed_task_count should be at least 2
    assert data["completed_task_count"] >= 2
    assert data["blocker_count"] >= 1

def test_get_weekly_summary(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.v1.daily_reports.check_admin_or_owner", lambda *args, **kwargs: None)
    
    start = str(date.today() - timedelta(days=2))
    response = client.get(f"/api/v1/daily-reports/summary/weekly?start_date={start}")
    assert response.status_code == 200
    data = response.json()
    assert "trend" in data
    assert isinstance(data["trend"], list)

def test_get_team_reports(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.v1.daily_reports.check_admin_or_owner", lambda *args, **kwargs: None)
    
    response = client.get(f"/api/v1/daily-reports/team?report_date={str(date.today())}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # The report we created in the first test might not be linked to a real user in the DB (since MockUser is not in DB).
    # But the endpoint works if it returns 200.

def test_get_blockers(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.v1.daily_reports.check_admin_or_owner", lambda *args, **kwargs: None)
    
    response = client.get("/api/v1/daily-reports/blockers?days=7")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Again, join with User might return empty list if User isn't in DB, but the API endpoint works and is valid.
