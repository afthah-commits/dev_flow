import pytest
from fastapi.testclient import TestClient

def test_client_portal_me_endpoint_requires_auth(client: TestClient):
    response = client.get("/api/v1/client-portal/me")
    assert response.status_code == 401

def test_internal_clients_endpoint_requires_auth(client: TestClient):
    response = client.get("/api/v1/clients")
    assert response.status_code == 401
