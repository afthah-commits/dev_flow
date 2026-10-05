import pytest
from uuid import uuid4, UUID
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.job import Job, JobExecution
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.core.security import create_access_token

@pytest.fixture
def auth_setup(db: Session):
    user = User(id=uuid4(), name='Test User', email='test@test.com', password_hash='pwd')
    org = Organization(id=uuid4(), name='Test Org', slug='test-org', created_by=user.id)
    db.add(user)
    db.commit()
    db.add(org)
    db.commit()
    db.commit()
    
    from app.models.organization import OrganizationRole
    member = OrganizationMember(organization_id=org.id, user_id=user.id, role=OrganizationRole.ADMIN)
    db.add(member)
    db.commit()
    
    token = create_access_token(user.id)
    return {
        "headers": {
            "Authorization": f"Bearer {token}",
            "X-Organization-Id": str(org.id)
        },
        "org_id": org.id,
        "user_id": user.id
    }

def test_list_jobs_empty(client: TestClient, db: Session, auth_setup: dict):
    response = client.get("/api/v1/jobs", headers=auth_setup["headers"])
    assert response.status_code == 200
    assert response.json() == []

def test_create_and_list_jobs(client: TestClient, db: Session, auth_setup: dict):
    org_id = auth_setup["org_id"]
    job = Job(
        id=uuid4(),
        organization_id=org_id,
        job_type="notification.dispatch",
        status="QUEUED"
    )
    db.add(job)
    db.commit()
    
    response = client.get("/api/v1/jobs", headers=auth_setup["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["job_type"] == "notification.dispatch"
    
def test_retry_job(client: TestClient, db: Session, auth_setup: dict):
    org_id = auth_setup["org_id"]
    job = Job(
        id=uuid4(),
        organization_id=org_id,
        job_type="notification.dispatch",
        status="FAILED"
    )
    db.add(job)
    db.commit()
    
    response = client.post(f"/api/v1/jobs/{job.id}/retry", headers=auth_setup["headers"])
    assert response.status_code == 200
    
    db.refresh(job)
    assert job.status == "QUEUED"
    assert job.attempts == 0

def test_cancel_job(client: TestClient, db: Session, auth_setup: dict):
    org_id = auth_setup["org_id"]
    job = Job(
        id=uuid4(),
        organization_id=org_id,
        job_type="notification.dispatch",
        status="QUEUED"
    )
    db.add(job)
    db.commit()
    
    response = client.post(f"/api/v1/jobs/{job.id}/cancel", headers=auth_setup["headers"])
    assert response.status_code == 200
    
    db.refresh(job)
    assert job.status == "CANCELLED"
