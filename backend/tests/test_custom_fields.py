import pytest
from fastapi.testclient import TestClient

def test_custom_fields_unauthorized(client: TestClient):
    response = client.get("/api/v1/custom-fields")
    assert response.status_code == 401
