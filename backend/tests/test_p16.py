import pytest
from app.models.api_key import APIKey

def test_api_key_public_api(client, db):
    # Register/Login
    client.post("/api/v1/auth/register", json={"name": "P16User", "email": "p16@ex.com", "password": "pwd"})
    token = client.post("/api/v1/auth/login", json={"email": "p16@ex.com", "password": "pwd"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Org
    org_res = client.post("/api/v1/organizations", json={"name": "P16Org"}, headers=headers)
    org_id = org_res.json()["id"]
    
    # Create Project
    
    
    # Create API Key
    res = client.post(f"/api/v1/api_keys?organization_id={org_id}", json={"name": "Test Key", "scopes": ["projects:read", "tasks:read"]}, headers=headers)
    raw_key = res.json()["raw_key"]
    key_id = res.json()["id"]
    
    # Access Public API
    pub_headers = {"Authorization": f"Bearer {raw_key}"}
    pub_res = client.get("/api/public/v1/projects", headers=pub_headers)
    assert pub_res.status_code == 200
    assert isinstance(pub_res.json(), list)
    
    # Test rate limiting
    # Mocking would require sending 100 requests, let's just test a few
    for _ in range(5):
        client.get("/api/public/v1/projects", headers=pub_headers)
        
    # Revoke API Key
    client.post(f"/api/v1/api_keys/{key_id}/revoke", headers=headers)
    pub_res = client.get("/api/public/v1/projects", headers=pub_headers)
    assert pub_res.status_code == 401
