import pytest
from uuid import uuid4

def test_integration_hub_apis(client, db):
    # Register and login user
    response = client.post("/api/v1/auth/register", json={
        "email": "inthub@example.com",
        "password": "Password123!",
        "full_name": "Hub User"
    })
    
    login_response = client.post("/api/v1/auth/login", data={
        "username": "inthub@example.com",
        "password": "Password123!"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create org
    org_response = client.post("/api/v1/organizations/", json={
        "name": "Int Org",
        "slug": "int-org"
    }, headers=headers)
    org_id = org_response.json()["id"]
    headers["X-Organization-Id"] = org_id

    # Add mock integration
    integ_resp = client.post("/api/v1/integrations", json={
        "provider": "SLACK",
        "name": "Mock Slack Test"
    }, headers=headers)
    assert integ_resp.status_code == 200
    integ_id = integ_resp.json()["id"]

    # Test enable/disable
    disable_resp = client.post(f"/api/v1/integrations/{integ_id}/disable", headers=headers)
    assert disable_resp.status_code == 200
    assert disable_resp.json()["enabled"] is False

    enable_resp = client.post(f"/api/v1/integrations/{integ_id}/enable", headers=headers)
    assert enable_resp.status_code == 200
    assert enable_resp.json()["enabled"] is True

    # Test integration directly
    test_resp = client.post(f"/api/v1/integrations/{integ_id}/test", headers=headers)
    assert test_resp.status_code == 200
    assert test_resp.json()["success"] is True

    # Fetch Usage
    usage_resp = client.get("/api/v1/integrations/usage/analytics", headers=headers)
    assert usage_resp.status_code == 200
    assert "total_requests" in usage_resp.json()

