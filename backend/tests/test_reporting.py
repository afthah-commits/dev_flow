import pytest
from uuid import uuid4

def test_reports_crud(client, db):
    # Register and login user
    response = client.post("/api/v1/auth/register", json={
        "email": "reportuser@example.com",
        "password": "Password123!",
        "full_name": "Report User"
    })
    
    login_response = client.post("/api/v1/auth/login", data={
        "username": "reportuser@example.com",
        "password": "Password123!"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create organization
    org_response = client.post("/api/v1/organizations/", json={
        "name": "Report Org",
        "slug": "report-org"
    }, headers=headers)
    org_id = org_response.json()["id"]
    headers["X-Organization-Id"] = org_id
    
    # Create report
    report_data = {
        "name": "Test Overview",
        "report_type": "PROJECT_OVERVIEW"
    }
    create_resp = client.post("/api/v1/reports/", json=report_data, headers=headers)
    assert create_resp.status_code == 200
    report_id = create_resp.json()["id"]
    
    # Get report
    get_resp = client.get(f"/api/v1/reports/{report_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Test Overview"
    
    # Get all reports
    list_resp = client.get("/api/v1/reports/", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    
    # Get data
    data_resp = client.post(f"/api/v1/reports/{report_id}/data", json={}, headers=headers)
    assert data_resp.status_code == 200
    assert "data" in data_resp.json()
    
    # Create dashboard
    dash_resp = client.post("/api/v1/dashboards/", json={
        "name": "Main Dashboard"
    }, headers=headers)
    assert dash_resp.status_code == 200
    dash_id = dash_resp.json()["id"]
    
    # Add widget
    widget_resp = client.post(f"/api/v1/dashboards/{dash_id}/widgets", json={
        "widget_type": "PROJECT_COUNT",
        "title": "Projects"
    }, headers=headers)
    assert widget_resp.status_code == 200
    assert widget_resp.json()["title"] == "Projects"

