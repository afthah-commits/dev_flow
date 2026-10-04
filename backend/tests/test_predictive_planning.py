import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.models.project import Project
from app.models.task import Task
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.core.security import create_access_token

@pytest.fixture
def auth_setup_predictive(db: Session):
    user = User(id=uuid4(), name='Pred User', email='pred@test.com', password_hash='pwd')
    db.add(user)
    db.commit()
    
    org = Organization(id=uuid4(), name='Pred Org', slug='pred-org', created_by=user.id)
    db.add(org)
    db.commit()
    
    member = OrganizationMember(organization_id=org.id, user_id=user.id, role="admin")
    db.add(member)
    db.commit()
    
    project = Project(id=uuid4(), name='Pred Project', slug='pred-project', organization_id=org.id, owner_id=user.id)
    db.add(project)
    db.commit()
    
    token = create_access_token(user.id)
    return {
        "headers": {
            "Authorization": f"Bearer {token}",
            "X-Organization-Id": str(org.id)
        },
        "org_id": org.id,
        "user_id": user.id,
        "project_id": project.id
    }

def test_forecast_calculations(client: TestClient, db: Session, auth_setup_predictive: dict):
    headers = auth_setup_predictive["headers"]
    project_id = auth_setup_predictive["project_id"]
    
    # Create some tasks
    now = datetime.now(timezone.utc)
    t1 = Task(id=uuid4(), project_id=project_id, task_key="PR-1", title="Task 1", status="DONE", updated_at=now, estimate_points=5, creator_id=auth_setup_predictive["user_id"])
    t2 = Task(id=uuid4(), project_id=project_id, task_key="PR-2", title="Task 2", status="TODO", updated_at=now, estimate_points=3, creator_id=auth_setup_predictive["user_id"])
    db.add_all([t1, t2])
    db.commit()
    
    res = client.get(f"/api/v1/ai/projects/{project_id}/forecast", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["remaining_tasks"] == 1
    assert data["completed_tasks"] == 1
    assert data["velocity"] > 0
    assert data["assumptions"]["unestimated_tasks"] == 0

def test_risk_scoring(client: TestClient, db: Session, auth_setup_predictive: dict):
    headers = auth_setup_predictive["headers"]
    project_id = auth_setup_predictive["project_id"]
    
    # Overdue task
    past = datetime.now(timezone.utc) - timedelta(days=5)
    t1 = Task(id=uuid4(), project_id=project_id, task_key="PR-3", title="Overdue", status="TODO", due_date=past, creator_id=auth_setup_predictive["user_id"])
    t2 = Task(id=uuid4(), project_id=project_id, task_key="PR-4", title="Blocked", status="TODO", is_blocked=True, creator_id=auth_setup_predictive["user_id"])
    db.add_all([t1, t2])
    db.commit()
    
    res = client.get(f"/api/v1/ai/projects/{project_id}/risk-engine", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["overall_risk_score"] > 0
    assert any(r["category"] == "SCHEDULE" for r in data["risks"])
    assert any(r["category"] == "WORKFLOW" for r in data["risks"])

def test_sprint_capacity(client: TestClient, db: Session, auth_setup_predictive: dict):
    headers = auth_setup_predictive["headers"]
    project_id = auth_setup_predictive["project_id"]
    
    res = client.get(f"/api/v1/ai/projects/{project_id}/sprint-planning", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "recommended_capacity_points" in data
    assert isinstance(data["suggested_tasks"], list)

def test_task_prioritization(client: TestClient, db: Session, auth_setup_predictive: dict):
    headers = auth_setup_predictive["headers"]
    project_id = auth_setup_predictive["project_id"]
    
    res = client.get(f"/api/v1/ai/projects/{project_id}/task-priorities", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

def test_organization_isolation(client: TestClient, db: Session, auth_setup_predictive: dict):
    # Try to access a project from another org
    other_org = Organization(id=uuid4(), name='Other', slug='other', created_by=auth_setup_predictive["user_id"])
    db.add(other_org)
    db.commit()
    other_project = Project(id=uuid4(), name='Other P', slug='other-p', organization_id=other_org.id, owner_id=auth_setup_predictive["user_id"])
    db.add(other_project)
    db.commit()
    
    res = client.get(f"/api/v1/ai/projects/{other_project.id}/forecast", headers=auth_setup_predictive["headers"])
    assert res.status_code == 404

def test_empty_project(client: TestClient, db: Session, auth_setup_predictive: dict):
    headers = auth_setup_predictive["headers"]
    project_id = auth_setup_predictive["project_id"]
    
    # DB is already practically empty for this project except tasks added in earlier tests... wait, fixtures aren't fully isolated? 
    # Usually `client` fixture rolls back. So it should be empty.
    res = client.get(f"/api/v1/ai/projects/{project_id}/forecast", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["remaining_tasks"] == 0
    assert data["completed_tasks"] == 0
