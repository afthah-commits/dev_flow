import os

def patch_tests():
    with open("backend/tests/api/v1/test_analytics_new.py", "a") as f:
        f.write("""
def test_analytics_query_trend(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.v1.analytics.check_permission", lambda *args, **kwargs: None)
    response = client.post(
        "/api/v1/analytics/query",
        json={"metric": "tasks.completed", "group_by": "date"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "tasks.completed"
    assert isinstance(data["data"], list)

def test_analytics_export_success(client: TestClient, db: Session, monkeypatch):
    monkeypatch.setattr("app.api.deps.require_organization_member", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.api.v1.analytics.check_permission", lambda *args, **kwargs: None)
    response = client.post(
        "/api/v1/analytics/export?format=csv",
        json={"metric": "sprint.velocity"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "csv"
    assert isinstance(data["data"], list)
""")

if __name__ == "__main__":
    patch_tests()
