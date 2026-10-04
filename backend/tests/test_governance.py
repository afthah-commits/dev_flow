import pytest
from uuid import uuid4

def test_governance_apis(client, db):
    # Register and login user
    response = client.post("/api/v1/auth/register", json={
        "email": "govuser@example.com",
        "password": "Password123!",
        "name": "Gov User"
    })
    print("REG:", response.status_code, response.text)
    
    login_response = client.post("/api/v1/auth/login", json={
        "email": "govuser@example.com",
        "password": "Password123!"
    })
    print("LOG:", login_response.status_code, login_response.text)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create org
    org_response = client.post("/api/v1/organizations/", json={
        "name": "Gov Org",
        "slug": "gov-org"
    }, headers=headers)
    org_id = org_response.json()["id"]
    headers["X-Organization-Id"] = org_id
    
    # Test Security Policy
    pol_resp = client.get("/api/v1/governance/security-policy", headers=headers)
    assert pol_resp.status_code == 200
    
    patch_resp = client.patch("/api/v1/governance/security-policy", json={"require_mfa": True}, headers=headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["require_mfa"] is True
    
    # Test Domains
    dom_resp = client.post("/api/v1/governance/domains", json={"domain": "example.com"}, headers=headers)
    assert dom_resp.status_code == 200
    dom_id = dom_resp.json()["id"]
    
    # Test Data Exports
    export_resp = client.post("/api/v1/governance/data-exports", json={"export_type": "AUDIT_LOGS"}, headers=headers)
    assert export_resp.status_code == 200
    
    # Privacy
    priv_resp = client.get("/api/v1/privacy/me", headers=headers)
    assert priv_resp.status_code == 200

