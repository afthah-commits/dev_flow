import pytest

def test_webhooks_integrations(client, db):
    # Register/Login
    client.post("/api/v1/auth/register", json={"name": "WHUser", "email": "wh@ex.com", "password": "pwd"})
    token = client.post("/api/v1/auth/login", json={"email": "wh@ex.com", "password": "pwd"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Org
    org_res = client.post("/api/v1/organizations", json={"name": "WHOrg"}, headers=headers)
    org_id = org_res.json()["id"]
    headers["X-Organization-Id"] = org_id
    
    # Webhook
    wh_res = client.post(f"/api/v1/webhooks?organization_id={org_id}", json={"name": "MyWH", "url": "http://mock", "active": True, "subscribed_events": ["*"]}, headers=headers)
    assert wh_res.status_code == 200
    
    # Integration
    int_res = client.post("/api/v1/integrations", json={"provider": "slack", "name": "Slack", "status": "ACTIVE"}, headers=headers)
    assert int_res.status_code == 200
