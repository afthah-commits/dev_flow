from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_register_user(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "password" not in data
    assert "password_hash" not in data

def test_register_duplicate_user(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Test User 2", "email": "duplicate@example.com", "password": "password123"}
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User 3", "email": "duplicate@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "The user with this username already exists in the system."

def test_login_valid_credentials(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Login User", "email": "login@example.com", "password": "password123"}
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_credentials(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "notfound@example.com", "password": "password123"}
    )
    assert response.status_code == 401

def test_get_current_user(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Me User", "email": "me@example.com", "password": "password123"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@example.com"

def test_unauthorized_access(client: TestClient):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
