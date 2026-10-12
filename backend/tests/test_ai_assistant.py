import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from uuid import uuid4

from app.services.ai.assistant import (
    resolve_relative_date, parse_task_intent, execute_create_task, find_target_project
)
from app.models.task import TaskPriority, TaskStatus, Task
from app.models.project import Project
from app.models.organization import Organization, OrganizationMember
from app.models.user import User


# ---------------------------------------------------------------------------
# Test 1 & 4: Natural-language intent extraction, priority & relative dates
# ---------------------------------------------------------------------------

def test_resolve_relative_date_handling():
    # Base date: Monday, October 12, 2026
    base_monday = datetime(2026, 10, 12, 10, 0, 0, tzinfo=timezone.utc)

    # Friday of current week -> October 16, 2026
    friday = resolve_relative_date("Create a task by Friday", base_date=base_monday)
    assert friday is not None
    assert friday.year == 2026
    assert friday.month == 10
    assert friday.day == 16
    assert friday.hour == 23 and friday.minute == 59 and friday.second == 59

    # Tomorrow -> October 13, 2026
    tomorrow = resolve_relative_date("Fix bug by tomorrow", base_date=base_monday)
    assert tomorrow is not None
    assert tomorrow.day == 13

    # In 3 days -> October 15, 2026
    in_3_days = resolve_relative_date("Deploy in 3 days", base_date=base_monday)
    assert in_3_days is not None
    assert in_3_days.day == 15

    # Explicit ISO date -> 2026-10-25
    iso_date = resolve_relative_date("Launch by 2026-10-25", base_date=base_monday)
    assert iso_date is not None
    assert iso_date.year == 2026 and iso_date.month == 10 and iso_date.day == 25


def test_parse_task_intent_extraction():
    # Example 1: High-priority task with relative due date
    res1 = parse_task_intent("Create a high-priority task to implement notifications by Friday.")
    assert res1 is not None
    assert res1["is_create_task"] is True
    assert res1["count"] == 1
    assert "Implement notifications" in res1["title"]
    assert res1["priority"] == TaskPriority.HIGH
    assert res1["due_date"] is not None

    # Example 2: Backend bug fix
    res2 = parse_task_intent("Add a task to fix the login bug in the backend.")
    assert res2 is not None
    assert "Fix the login bug in the backend" in res2["title"]
    assert res2["priority"] == TaskPriority.MEDIUM

    # Example 3: Critical blocker
    res3 = parse_task_intent("Add a critical task: Patch security vulnerability in auth service.")
    assert res3 is not None
    assert res3["priority"] == TaskPriority.CRITICAL

    # Example 4: Multi-task creation
    res4 = parse_task_intent("Create three tasks for implementing user authentication.")
    assert res4 is not None
    assert res4["count"] == 3
    assert "Implementing user authentication" in res4["title"] or "User authentication" in res4["title"]

    # Non-task instruction should return None
    res_none = parse_task_intent("What is the current velocity of our sprint?")
    assert res_none is None


# ---------------------------------------------------------------------------
# Test 2 & 5: Real task creation with actual ID and task_key returned
# ---------------------------------------------------------------------------

def test_api_natural_language_task_creation(client: TestClient):
    # Register & Login
    client.post("/api/v1/auth/register", json={"name": "PM User", "email": "pm@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "pm@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Org & Project
    org_res = client.post("/api/v1/organizations", json={"name": "Engineering Org"}, headers=headers)
    org_id = org_res.json()["id"]
    headers["X-Organization-Id"] = org_id

    proj_res = client.post("/api/v1/projects", json={"name": "DevFlow Core", "key": "CORE"}, headers=headers)
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # Create Conversation scoped to project
    conv_res = client.post("/api/v1/ai/conversations", json={"title": "PM Chat", "project_id": proj_id}, headers=headers)
    conv_id = conv_res.json()["id"]

    # Natural language task creation request
    msg_payload = {"message": "Create a high-priority task to implement notifications by Friday."}
    msg_res = client.post(f"/api/v1/ai/conversations/{conv_id}/messages", json=msg_payload, headers=headers)
    assert msg_res.status_code == 200
    data = msg_res.json()

    assert "Task Created Successfully" in data["content"]
    assert "CORE-" in data["content"]
    assert "Implement notifications" in data["content"]
    assert "HIGH" in data["content"]

    # Verify action_data contains real task ID and task key
    assert data["action_data"] is not None
    assert data["action_data"]["type"] == "task_created"
    created_tasks = data["action_data"]["created_tasks"]
    assert len(created_tasks) == 1
    task_id = created_tasks[0]["id"]
    task_key = created_tasks[0]["key"]
    assert task_key.startswith("CORE-")

    # Verify task actually exists in DB via task endpoint
    get_task = client.get(f"/api/v1/projects/{proj_id}/tasks", headers=headers)
    assert get_task.status_code == 200
    tasks = get_task.json().get("items", [])
    matched = [t for t in tasks if t["id"] == task_id]
    assert len(matched) == 1
    assert matched[0]["priority"] == "HIGH"
    assert "notifications" in matched[0]["title"].lower()


# ---------------------------------------------------------------------------
# Test 3: Ambiguous project clarification
# ---------------------------------------------------------------------------

def test_ambiguous_project_clarification(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "Multi User", "email": "multi@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "multi@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    org_res = client.post("/api/v1/organizations", json={"name": "Multi Project Org"}, headers=headers)
    org_id = org_res.json()["id"]
    headers["X-Organization-Id"] = org_id

    # Create two projects
    client.post("/api/v1/projects", json={"name": "Web Frontend", "key": "WEB"}, headers=headers)
    client.post("/api/v1/projects", json={"name": "Mobile App", "key": "MOB"}, headers=headers)

    # Conversation without project_id
    conv_res = client.post("/api/v1/ai/conversations", json={"title": "Global Chat"}, headers=headers)
    conv_id = conv_res.json()["id"]

    # Task creation request without specifying which project
    msg_res = client.post(
        f"/api/v1/ai/conversations/{conv_id}/messages",
        json={"message": "Add a task to fix the header alignment."},
        headers=headers
    )
    assert msg_res.status_code == 200
    content = msg_res.json()["content"]

    # Must ask for clarification rather than creating a task in arbitrary project
    assert "Which project should I add this task to?" in content
    assert "Web Frontend" in content
    assert "Mobile App" in content


# ---------------------------------------------------------------------------
# Test 6: Failed task creation does not report success
# ---------------------------------------------------------------------------

def test_failed_task_creation_rolls_back(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "Rollback User", "email": "rb@example.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "rb@example.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    org_res = client.post("/api/v1/organizations", json={"name": "Rollback Org"}, headers=headers)
    headers["X-Organization-Id"] = org_res.json()["id"]

    proj_res = client.post("/api/v1/projects", json={"name": "RB Proj", "key": "RB"}, headers=headers)
    pid = proj_res.json()["id"]

    conv_res = client.post("/api/v1/ai/conversations", json={"title": "RB Chat", "project_id": pid}, headers=headers)
    cid = conv_res.json()["id"]

    # Simulate DB commit failure in execute_create_task
    with patch("app.services.ai.assistant.execute_create_task", side_effect=Exception("Database write failure")):
        msg_res = client.post(
            f"/api/v1/ai/conversations/{cid}/messages",
            json={"message": "Create a task to build database backups."},
            headers=headers
        )
        assert msg_res.status_code == 200
        assert "Task Created Successfully" not in msg_res.json()["content"]
        assert "Failed to create task" in msg_res.json()["content"]


# ---------------------------------------------------------------------------
# Test 8 & 9: Unauthorized task creation and organization isolation
# ---------------------------------------------------------------------------

def test_organization_isolation_in_assistant(client: TestClient):
    # Org 1 with user 1
    client.post("/api/v1/auth/register", json={"name": "Org1 User", "email": "org1@example.com", "password": "password123"})
    res1 = client.post("/api/v1/auth/login", json={"email": "org1@example.com", "password": "password123"})
    h1 = {"Authorization": f"Bearer {res1.json()['access_token']}"}
    o1 = client.post("/api/v1/organizations", json={"name": "Org One"}, headers=h1).json()["id"]
    h1["X-Organization-Id"] = o1
    p1 = client.post("/api/v1/projects", json={"name": "Secret Project 1", "key": "SEC1"}, headers=h1).json()["id"]

    # Org 2 with user 2
    client.post("/api/v1/auth/register", json={"name": "Org2 User", "email": "org2@example.com", "password": "password123"})
    res2 = client.post("/api/v1/auth/login", json={"email": "org2@example.com", "password": "password123"})
    h2 = {"Authorization": f"Bearer {res2.json()['access_token']}"}
    o2 = client.post("/api/v1/organizations", json={"name": "Org Two"}, headers=h2).json()["id"]
    h2["X-Organization-Id"] = o2

    # User 2 tries to start a conversation on Project 1 (belongs to Org 1)
    unauthorized_conv = client.post("/api/v1/ai/conversations", json={"title": "Hacked Chat", "project_id": p1}, headers=h2)
    assert unauthorized_conv.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Test 10: Gemini error handling (missing credentials / rate limits)
# ---------------------------------------------------------------------------

def test_missing_gemini_api_key_graceful_notice(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "Notice User", "email": "notice@example.com", "password": "password123"})
    res = client.post("/api/v1/auth/login", json={"email": "notice@example.com", "password": "password123"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    org = client.post("/api/v1/organizations", json={"name": "Notice Org"}, headers=headers).json()["id"]
    headers["X-Organization-Id"] = org
    proj = client.post("/api/v1/projects", json={"name": "Notice Proj", "key": "NOT"}, headers=headers).json()["id"]

    conv = client.post("/api/v1/ai/conversations", json={"title": "Notice Chat", "project_id": proj}, headers=headers).json()["id"]

    # Test that general question when Gemini key is missing returns clear setup instructions
    from fastapi import HTTPException
    with patch("app.api.v1.ai.get_ai_provider") as mock_prov:
        prov_instance = MagicMock()
        prov_instance.chat = AsyncMock(side_effect=HTTPException(status_code=500, detail="Gemini API key is not configured."))
        mock_prov.return_value = prov_instance

        msg = client.post(
            f"/api/v1/ai/conversations/{conv}/messages",
            json={"message": "Can you advise on microservice design?"},
            headers=headers
        )
        assert msg.status_code == 200
        content = msg.json()["content"]
        assert "Gemini AI Provider Notice" in content
        assert "GEMINI_API_KEY" in content


# ---------------------------------------------------------------------------
# Test 11: Conversation history persistence
# ---------------------------------------------------------------------------

def test_conversation_history_persistence(client: TestClient):
    client.post("/api/v1/auth/register", json={"name": "Hist User", "email": "hist@example.com", "password": "password123"})
    res = client.post("/api/v1/auth/login", json={"email": "hist@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    org = client.post("/api/v1/organizations", json={"name": "Hist Org"}, headers=headers).json()["id"]
    headers["X-Organization-Id"] = org
    proj = client.post("/api/v1/projects", json={"name": "Hist Proj", "key": "HST"}, headers=headers).json()["id"]

    conv = client.post("/api/v1/ai/conversations", json={"title": "History Chat", "project_id": proj}, headers=headers).json()["id"]

    # Send 2 messages
    client.post(f"/api/v1/ai/conversations/{conv}/messages", json={"message": "Show overdue tasks"}, headers=headers)
    client.post(f"/api/v1/ai/conversations/{conv}/messages", json={"message": "What should I work on today?"}, headers=headers)

    # Fetch conversation details
    detail = client.get(f"/api/v1/ai/conversations/{conv}", headers=headers)
    assert detail.status_code == 200
    messages = detail.json().get("messages", [])
    # 2 user messages + 2 assistant messages = 4
    assert len(messages) == 4
    roles = [m["role"] for m in messages]
    assert roles == ["user", "assistant", "user", "assistant"]
