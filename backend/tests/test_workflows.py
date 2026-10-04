import pytest
from fastapi.testclient import TestClient

def test_workflows_unauthorized_access(client: TestClient):
    response = client.get("/api/v1/workflows")
    assert response.status_code == 401
