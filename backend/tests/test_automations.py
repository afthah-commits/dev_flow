import pytest
from app.models.automation import Automation
from app.services.automation_engine import handle_event

def test_automation_crud(client, db):
    # Register/Login
    res = client.post("/api/v1/auth/register", json={"name": "AutoUser", "email": "auto@ex.com", "password": "pwd"})
    token = client.post("/api/v1/auth/login", json={"email": "auto@ex.com", "password": "pwd"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Org
    org_res = client.post("/api/v1/organizations", json={"name": "AutoOrg"}, headers=headers)
    org_id = org_res.json()["id"]
    
    # Create Automation
    auto_data = {
        "name": "Test Auto",
        "trigger_type": "TASK_STATUS_CHANGED",
        "actions": [{"type": "CREATE_COMMENT", "content": "Hello"}],
        "enabled": True
    }
    res = client.post(f"/api/v1/automations?organization_id={org_id}", json=auto_data, headers=headers)
    assert res.status_code == 200
    auto_id = res.json()["id"]
    
    # List Automations
    res = client.get(f"/api/v1/automations?organization_id={org_id}", headers=headers)
    assert len(res.json()) == 1
    

