"""Phase 31 — cross-tenant isolation, RBAC and API security regression tests.

Covers the modules hardened in Phase 31 (automations, api_keys, webhooks,
knowledge, ai, dashboards, admin) plus MEMBER / CUSTOM-role RBAC and the
401 unauthenticated convention. Workflow cross-org isolation is already
covered by test_workflow_studio.py (Phase 30).
"""
from uuid import uuid4, UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization import OrganizationMember, OrganizationRole
from app.models.job import Job


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register(client: TestClient, email: str) -> dict:
    client.post("/api/v1/auth/register",
                json={"name": email.split("@")[0], "email": email, "password": "password123"})
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _make_org(client: TestClient, auth_headers: dict, name: str):
    org = client.post("/api/v1/organizations", json={"name": name}, headers=auth_headers).json()
    return org["id"], {**auth_headers, "X-Organization-Id": org["id"]}


def _add_member(db: Session, org_id: str, user_email: str, role: OrganizationRole) -> OrganizationMember:
    user = db.query(User).filter(User.email == user_email).first()
    member = OrganizationMember(organization_id=UUID(str(org_id)), user_id=user.id, role=role)
    db.add(member)
    db.commit()
    return member


# ---------------------------------------------------------------------------
# Tenant isolation — automations (hardened in Phase 31)
# ---------------------------------------------------------------------------

def test_automations_cross_org_isolation(client: TestClient):
    headers_a = _register(client, "iso-auto-a@example.com")
    org_a, headers_a = _make_org(client, headers_a, "Auto Org A")
    headers_b = _register(client, "iso-auto-b@example.com")
    org_b, headers_b = _make_org(client, headers_b, "Auto Org B")

    payload = {
        "name": "Org A Secret Automation",
        "trigger_type": "TASK_STATUS_CHANGED",
        "actions": [{"type": "CREATE_COMMENT", "content": "hi"}],
        "enabled": True,
    }
    res = client.post(f"/api/v1/automations?organization_id={org_a}", json=payload, headers=headers_a)
    assert res.status_code == 200, res.text
    automation_id = res.json()["id"]

    # B cannot list or create inside ORG-A
    assert client.get(f"/api/v1/automations?organization_id={org_a}", headers=headers_b).status_code == 403
    assert client.post(f"/api/v1/automations?organization_id={org_a}", json=payload, headers=headers_b).status_code == 403

    # B cannot read/update/delete/test/inspect executions of A's automation
    assert client.get(f"/api/v1/automations/{automation_id}", headers=headers_b).status_code in (403, 404)
    assert client.patch(f"/api/v1/automations/{automation_id}", json={"name": "hijack"}, headers=headers_b).status_code in (403, 404)
    assert client.delete(f"/api/v1/automations/{automation_id}", headers=headers_b).status_code in (403, 404)
    assert client.get(f"/api/v1/automations/{automation_id}/executions", headers=headers_b).status_code in (403, 404)
    assert client.post(f"/api/v1/automations/{automation_id}/test", json={"status": "DONE"}, headers=headers_b).status_code in (403, 404)

    # A still has full access; B's own org list works and never contains A's automation
    assert client.get(f"/api/v1/automations?organization_id={org_a}", headers=headers_a).status_code == 200
    res = client.get(f"/api/v1/automations?organization_id={org_b}", headers=headers_b)
    assert res.status_code == 200
    assert all(a["id"] != automation_id for a in res.json())


# ---------------------------------------------------------------------------
# Tenant isolation — API keys (hardened in Phase 31)
# ---------------------------------------------------------------------------

def test_api_keys_cross_org_isolation(client: TestClient):
    headers_a = _register(client, "iso-key-a@example.com")
    org_a, headers_a = _make_org(client, headers_a, "Key Org A")
    headers_b = _register(client, "iso-key-b@example.com")
    _org_b, headers_b = _make_org(client, headers_b, "Key Org B")

    res = client.post(f"/api/v1/api_keys?organization_id={org_a}",
                      json={"name": "A key", "scopes": ["read"]}, headers=headers_a)
    assert res.status_code == 200, res.text
    created = res.json()
    key_id = created["id"]
    assert "raw_key" in created  # exposed exactly once at creation

    # Listing never exposes the raw key or its hash
    res = client.get(f"/api/v1/api_keys?organization_id={org_a}", headers=headers_a)
    assert res.status_code == 200
    for k in res.json():
        assert "raw_key" not in k
        assert "key_hash" not in k

    # B is locked out of ORG-A's key material
    assert client.get(f"/api/v1/api_keys?organization_id={org_a}", headers=headers_b).status_code == 403
    assert client.post(f"/api/v1/api_keys?organization_id={org_a}",
                       json={"name": "evil", "scopes": ["write"]}, headers=headers_b).status_code == 403
    assert client.post(f"/api/v1/api_keys/{key_id}/revoke", headers=headers_b).status_code in (403, 404)

    # A can revoke its own key
    assert client.post(f"/api/v1/api_keys/{key_id}/revoke", headers=headers_a).status_code == 200


# ---------------------------------------------------------------------------
# Tenant isolation — webhooks (hardened in Phase 31)
# ---------------------------------------------------------------------------

def test_webhooks_cross_org_isolation(client: TestClient):
    headers_a = _register(client, "iso-hook-a@example.com")
    org_a, headers_a = _make_org(client, headers_a, "Hook Org A")
    headers_b = _register(client, "iso-hook-b@example.com")
    _org_b, headers_b = _make_org(client, headers_b, "Hook Org B")

    payload = {"name": "A hook", "url": "https://example.com/hook", "active": True,
               "subscribed_events": ["task.created"]}
    res = client.post(f"/api/v1/webhooks?organization_id={org_a}", json=payload, headers=headers_a)
    assert res.status_code == 200, res.text
    webhook_id = res.json()["id"]
    # Response schema must not leak the signing secret
    assert "encrypted_secret" not in res.json()
    assert "secret" not in res.json()

    assert client.get(f"/api/v1/webhooks?organization_id={org_a}", headers=headers_b).status_code == 403
    assert client.post(f"/api/v1/webhooks?organization_id={org_a}", json=payload, headers=headers_b).status_code == 403
    assert client.delete(f"/api/v1/webhooks/{webhook_id}", headers=headers_b).status_code in (403, 404)

    assert client.get(f"/api/v1/webhooks?organization_id={org_a}", headers=headers_a).status_code == 200
    assert client.delete(f"/api/v1/webhooks/{webhook_id}", headers=headers_a).status_code == 200


# ---------------------------------------------------------------------------
# Tenant isolation — header-swap attacks on X-Organization-Id modules
# ---------------------------------------------------------------------------

def test_knowledge_cross_org_header_blocked(client: TestClient):
    headers_a = _register(client, "iso-know-a@example.com")
    _org_a, headers_a = _make_org(client, headers_a, "Know Org A")
    headers_b = _register(client, "iso-know-b@example.com")
    _org_b, _ = _make_org(client, headers_b, "Know Org B")

    # B swaps A's org id into the header: read and write must both be blocked
    res = client.get("/api/v1/knowledge/spaces", headers=headers_b)
    assert res.status_code in (403, 400)
    res = client.post("/api/v1/knowledge/spaces", json={"name": "Injected"}, headers=headers_b)
    assert res.status_code in (403, 400)

    # Missing header entirely is rejected too
    no_org = {k: v for k, v in headers_b.items() if k != "X-Organization-Id"}
    assert client.get("/api/v1/knowledge/spaces", headers=no_org).status_code == 400


def test_ai_cross_org_header_blocked(client: TestClient):
    headers_a = _register(client, "iso-ai-a@example.com")
    _org_a, _ = _make_org(client, headers_a, "AI Org A")
    headers_b = _register(client, "iso-ai-b@example.com")
    _org_b, _ = _make_org(client, headers_b, "AI Org B")

    # B sends A's org id — AI usage/summary endpoints must refuse
    res = client.get("/api/v1/ai/usage", headers=headers_b)
    assert res.status_code in (400, 403)


def test_dashboards_cross_org_header_blocked(client: TestClient):
    headers_a = _register(client, "iso-dash-a@example.com")
    _org_a, headers_a = _make_org(client, headers_a, "Dash Org A")
    headers_b = _register(client, "iso-dash-b@example.com")
    _org_b, headers_b = _make_org(client, headers_b, "Dash Org B")

    # B uses its own token but A's org header
    res = client.get("/api/v1/dashboards/", headers={**headers_b, "X-Organization-Id": headers_a["X-Organization-Id"]})
    assert res.status_code in (400, 403)
    res = client.post("/api/v1/dashboards/", json={"name": "Injected"},
                      headers={**headers_b, "X-Organization-Id": headers_a["X-Organization-Id"]})
    assert res.status_code in (400, 403)


# ---------------------------------------------------------------------------
# Admin system stats scoped to caller's organizations
# ---------------------------------------------------------------------------

def test_admin_system_scoped_to_own_organizations(client: TestClient, db: Session):
    headers_a = _register(client, "iso-admin-a@example.com")
    org_a, headers_a = _make_org(client, headers_a, "Admin Org A")
    headers_b = _register(client, "iso-admin-b@example.com")
    org_b, headers_b = _make_org(client, headers_b, "Admin Org B")

    # Two FAILED jobs in ORG-A, one in ORG-B
    for _ in range(2):
        db.add(Job(organization_id=UUID(str(org_a)), job_type="test.job", status="FAILED"))
    db.add(Job(organization_id=UUID(str(org_b)), job_type="test.job", status="FAILED"))
    db.commit()

    res_b = client.get("/api/v1/admin/system", headers=headers_b)
    assert res_b.status_code == 200, res_b.text
    stats_b = res_b.json()
    # B belongs only to ORG-B: sees its own job, never ORG-A's
    assert stats_b["jobs"]["failed"] == 1, stats_b["jobs"]

    res_a = client.get("/api/v1/admin/system", headers=headers_a)
    assert res_a.status_code == 200, res_a.text
    assert res_a.json()["jobs"]["failed"] == 2


def test_admin_system_requires_org_membership(client: TestClient):
    headers = _register(client, "iso-admin-none@example.com")
    # User with no organization cannot read system stats
    assert client.get("/api/v1/admin/system", headers=headers).status_code == 403


# ---------------------------------------------------------------------------
# Unauthenticated convention: 401 everywhere
# ---------------------------------------------------------------------------

def test_unauthenticated_returns_401(client: TestClient):
    for method, url, kwargs in [
        ("get", "/api/v1/automations?organization_id=x", {}),
        ("get", "/api/v1/api_keys?organization_id=x", {}),
        ("get", "/api/v1/webhooks?organization_id=x", {}),
        ("get", "/api/v1/knowledge/spaces", {}),
        ("get", "/api/v1/ai/usage", {}),
        ("get", "/api/v1/admin/system", {}),
        ("get", "/api/v1/dashboards/", {}),
        ("get", "/api/v1/workflows", {}),
    ]:
        res = getattr(client, method)(url, **kwargs)
        assert res.status_code == 401, f"{method.upper()} {url} -> {res.status_code}"


# ---------------------------------------------------------------------------
# RBAC: OWNER vs MEMBER vs CUSTOM ROLE
# ---------------------------------------------------------------------------

def test_member_rbac_dashboards_and_roles(client: TestClient, db: Session):
    headers_owner = _register(client, "rbac-owner@example.com")
    org_id, headers_owner = _make_org(client, headers_owner, "RBAC Org")

    headers_member = _register(client, "rbac-member@example.com")
    _add_member(db, org_id, "rbac-member@example.com", OrganizationRole.MEMBER)
    headers_member = {**headers_member, "X-Organization-Id": org_id}

    # OWNER can create dashboards and custom roles
    res = client.post("/api/v1/dashboards/", json={"name": "Owner Board"}, headers=headers_owner)
    assert res.status_code == 200, res.text
    res = client.post(f"/api/v1/roles/{org_id}/roles",
                      json={"name": "Viewer", "permissions": ["dashboards.view"]}, headers=headers_owner)
    assert res.status_code == 200, res.text

    # Plain MEMBER has no explicit permission: blocked from manage and view
    assert client.post("/api/v1/dashboards/", json={"name": "Member Board"}, headers=headers_member).status_code == 403
    assert client.get("/api/v1/dashboards/", headers=headers_member).status_code == 403
    # MEMBER cannot create custom roles
    assert client.post(f"/api/v1/roles/{org_id}/roles",
                       json={"name": "Evil", "permissions": ["*"]}, headers=headers_member).status_code == 403
    # MEMBER can read the roles catalog (membership only)
    assert client.get(f"/api/v1/roles/{org_id}/roles", headers=headers_member).status_code == 200


def test_custom_role_grants_specific_permission(client: TestClient, db: Session):
    headers_owner = _register(client, "crb-owner@example.com")
    org_id, headers_owner = _make_org(client, headers_owner, "CRB Org")

    headers_member = _register(client, "crb-member@example.com")
    member = _add_member(db, org_id, "crb-member@example.com", OrganizationRole.MEMBER)
    headers_member = {**headers_member, "X-Organization-Id": org_id}

    # Baseline: plain MEMBER blocked
    assert client.post("/api/v1/dashboards/", json={"name": "No"}, headers=headers_member).status_code == 403

    # Owner grants dashboards.view + dashboards.manage via a Phase 17 custom role
    res = client.post(f"/api/v1/roles/{org_id}/roles",
                      json={"name": "Dash Editor", "permissions": ["dashboards.view", "dashboards.manage"]},
                      headers=headers_owner)
    assert res.status_code == 200, res.text
    role_id = res.json()["id"]

    member.custom_role_id = UUID(str(role_id))
    db.commit()

    # Same member now passes check_permission
    res = client.get("/api/v1/dashboards/", headers=headers_member)
    assert res.status_code == 200, res.text
    res = client.post("/api/v1/dashboards/", json={"name": "Member Board"}, headers=headers_member)
    assert res.status_code == 200, res.text


def test_member_workflow_publish_blocked(client: TestClient, db: Session):
    headers_owner = _register(client, "wfrbac-owner@example.com")
    org_id, headers_owner = _make_org(client, headers_owner, "WF RBAC Org")

    res = client.post("/api/v1/workflows",
                      json={"name": "RBAC WF", "entity_type": "TASK", "states": [], "transitions": []},
                      headers=headers_owner)
    assert res.status_code == 201, res.text
    workflow_id = res.json()["id"]

    headers_member = _register(client, "wfrbac-member@example.com")
    _add_member(db, org_id, "wfrbac-member@example.com", OrganizationRole.MEMBER)
    headers_member = {**headers_member, "X-Organization-Id": org_id}

    # MEMBER: workflows.view allowed; workflows.create/publish require OWNER/ADMIN
    assert client.get("/api/v1/workflows", headers=headers_member).status_code == 200
    assert client.get(f"/api/v1/workflows/{workflow_id}", headers=headers_member).status_code == 200
    assert client.post("/api/v1/workflows",
                       json={"name": "Member WF", "entity_type": "TASK", "states": [], "transitions": []},
                       headers=headers_member).status_code == 403
    assert client.post(f"/api/v1/workflows/{workflow_id}/publish", headers=headers_member).status_code == 403
