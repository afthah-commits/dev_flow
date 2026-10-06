"""Phase 45 — Advanced Dashboard Customization (personal layout preferences).

Covers:
- default layout (no preferences saved)
- save / load / update / reset layout
- user isolation (layouts are per-user)
- organization isolation (same user, different orgs → separate layouts)
- unknown/stale widget ID handling
- permission-restricted widget handling (analytics.view)
- malformed payload rejection
- layout size limit
- auth (401) and missing org header
"""
from uuid import uuid4

from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.security import Role, RolePermission
from app.models.dashboard import DashboardLayout

URL = "/api/v1/dashboard/layout"


def _register(client, email):
    client.post("/api/v1/auth/register", json={"name": "P45 User", "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _org_with_user(db, client, email, role=OrganizationRole.OWNER):
    headers = _register(client, email)
    user = db.query(User).filter(User.email == email).first()
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=f"p45-{uuid4().hex[:8]}", created_by=user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id, role=role))
    db.commit()
    return headers, user, org


def _member_role(db, org, with_analytics_view=False):
    """Custom role for MEMBER users; optionally grants analytics.view."""
    role = Role(id=uuid4(), organization_id=org.id, name=f"role-{uuid4().hex[:6]}")
    db.add(role)
    db.flush()
    if with_analytics_view:
        db.add(RolePermission(id=uuid4(), role_id=role.id, permission="analytics.view"))
    db.commit()
    return role


# ---------------------------------------------------------------------------
# Auth / org context
# ---------------------------------------------------------------------------

def test_layout_requires_authentication(client):
    assert client.get(URL).status_code == 401
    assert client.put(URL, json={"widgets": []}).status_code == 401
    assert client.delete(URL).status_code == 401


def test_layout_requires_org_header(client):
    headers = _register(client, "p45-noorg@example.com")
    assert client.get(URL, headers=headers).status_code in (400, 403)


# ---------------------------------------------------------------------------
# Defaults / save / load / update / reset
# ---------------------------------------------------------------------------

def test_get_default_layout_when_nothing_saved(client, db):
    headers, user, org = _org_with_user(db, client, "p45-default@example.com")
    res = client.get(URL, headers={**headers, "X-Organization-Id": str(org.id)})
    assert res.status_code == 200
    body = res.json()
    assert body["customized"] is False
    ids = [w["id"] for w in body["widgets"]]
    assert ids == ["stats", "active_sprints", "recent_projects"]
    assert all(w["visible"] for w in body["widgets"])
    assert body["defaults"] == ["stats", "active_sprints", "recent_projects"]
    # nothing persisted
    assert db.query(DashboardLayout).count() == 0


def test_save_and_load_layout(client, db):
    headers, user, org = _org_with_user(db, client, "p45-save@example.com")
    h = {**headers, "X-Organization-Id": str(org.id)}

    payload = {"widgets": [
        {"id": "recent_projects", "visible": True},
        {"id": "stats", "visible": False},
    ]}
    res = client.put(URL, json=payload, headers=h)
    assert res.status_code == 200
    assert res.json()["customized"] is True

    loaded = client.get(URL, headers=h).json()
    assert [w["id"] for w in loaded["widgets"]] == ["recent_projects", "stats"]
    assert loaded["widgets"][1]["visible"] is False
    assert loaded["customized"] is True
    assert db.query(DashboardLayout).filter(DashboardLayout.user_id == user.id).count() == 1


def test_update_layout_overwrites_previous(client, db):
    headers, user, org = _org_with_user(db, client, "p45-update@example.com")
    h = {**headers, "X-Organization-Id": str(org.id)}
    client.put(URL, json={"widgets": [{"id": "stats", "visible": True}]}, headers=h)
    client.put(URL, json={"widgets": [{"id": "active_sprints", "visible": True},
                                       {"id": "stats", "visible": False}]}, headers=h)
    loaded = client.get(URL, headers=h).json()
    assert [w["id"] for w in loaded["widgets"]] == ["active_sprints", "stats"]
    assert db.query(DashboardLayout).filter(DashboardLayout.user_id == user.id).count() == 1


def test_reset_layout_restores_defaults(client, db):
    headers, user, org = _org_with_user(db, client, "p45-reset@example.com")
    h = {**headers, "X-Organization-Id": str(org.id)}
    client.put(URL, json={"widgets": [{"id": "active_sprints", "visible": False}]}, headers=h)
    assert db.query(DashboardLayout).count() == 1

    res = client.delete(URL, headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["customized"] is False
    assert [w["id"] for w in body["widgets"]] == ["stats", "active_sprints", "recent_projects"]
    assert db.query(DashboardLayout).count() == 0
    # GET after reset returns defaults again
    assert client.get(URL, headers=h).json()["customized"] is False


# ---------------------------------------------------------------------------
# Isolation
# ---------------------------------------------------------------------------

def test_user_isolation(client, db):
    h1, user1, org = _org_with_user(db, client, "p45-iso1@example.com")
    _, user2, _ = _org_with_user(db, client, "p45-iso2@example.com")
    h2 = {**_register(client, "p45-iso2@example.com"), "X-Organization-Id": str(org.id)}
    # add user2 as member of org
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user2.id, role=OrganizationRole.MEMBER))
    db.commit()

    client.put(URL, json={"widgets": [{"id": "active_sprints", "visible": False}]},
               headers={**h1, "X-Organization-Id": str(org.id)})

    # user2 gets their own (permission-filtered) defaults, not user1's layout
    other = client.get(URL, headers=h2).json()
    assert other["customized"] is False
    # user2 is a plain MEMBER: analytics.view-gated "stats" is filtered out
    assert [w["id"] for w in other["widgets"]] == ["active_sprints", "recent_projects"]


def test_organization_isolation(client, db):
    headers, user, org_a = _org_with_user(db, client, "p45-orgiso@example.com")
    org_b = Organization(id=uuid4(), name=f"Org B {uuid4().hex[:6]}",
                         slug=f"p45-b-{uuid4().hex[:8]}", created_by=user.id)
    db.add(org_b)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org_b.id, user_id=user.id, role=OrganizationRole.OWNER))
    db.commit()

    client.put(URL, json={"widgets": [{"id": "active_sprints", "visible": False}]},
               headers={**headers, "X-Organization-Id": str(org_a.id)})
    other_org = client.get(URL, headers={**headers, "X-Organization-Id": str(org_b.id)}).json()
    assert other_org["customized"] is False
    assert db.query(DashboardLayout).count() == 1


# ---------------------------------------------------------------------------
# Validation & safety
# ---------------------------------------------------------------------------

def test_unknown_widget_ids_ignored_safely(client, db):
    headers, user, org = _org_with_user(db, client, "p45-unknown@example.com")
    h = {**headers, "X-Organization-Id": str(org.id)}
    payload = {"widgets": [
        {"id": "removed_widget_xyz", "visible": True},   # stale widget
        {"id": "stats", "visible": False},
        {"id": "'; DROP TABLE dashboard_layouts;--", "visible": True},
    ]}
    res = client.put(URL, json=payload, headers=h)
    assert res.status_code == 200
    saved = client.get(URL, headers=h).json()
    assert [w["id"] for w in saved["widgets"]] == ["stats"]
    assert saved["widgets"][0]["visible"] is False


def test_permission_restricted_widget_hidden_from_members(client, db):
    """'stats' requires analytics.view; plain MEMBERs never get it."""
    # OWNER (implicit analytics.view) saves a layout including the gated widget
    headers, user, org = _org_with_user(db, client, "p45-perm-owner@example.com")
    h = {**headers, "X-Organization-Id": str(org.id)}
    res = client.put(URL, json={"widgets": [
        {"id": "recent_projects", "visible": False},
        {"id": "stats", "visible": True},
    ]}, headers=h)
    assert res.status_code == 200
    assert [w["id"] for w in res.json()["widgets"]] == ["recent_projects", "stats"]

    # MEMBER without the permission: default layout excludes the gated widget
    member_headers = _register(client, "p45-perm-member@example.com")
    member_user = db.query(User).filter(User.email == "p45-perm-member@example.com").first()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=member_user.id, role=OrganizationRole.MEMBER))
    db.commit()
    hm = {**member_headers, "X-Organization-Id": str(org.id)}
    defaults = client.get(URL, headers=hm).json()
    assert "stats" not in [w["id"] for w in defaults["widgets"]]

    # MEMBER cannot save a restricted widget either — silently dropped
    res = client.put(URL, json={"widgets": [
        {"id": "stats", "visible": True},
        {"id": "recent_projects", "visible": False},
    ]}, headers=hm)
    assert res.status_code == 200
    assert [w["id"] for w in res.json()["widgets"]] == ["recent_projects"]


def test_permission_restricted_widget_allowed_with_custom_role(client, db):
    headers, user, org = _org_with_user(db, client, "p45-role-member@example.com", role=OrganizationRole.MEMBER)
    _member_role(db, org, with_analytics_view=True)
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org.id,
        OrganizationMember.user_id == user.id,
    ).first()
    member.custom_role_id = None  # will set below
    role = _member_role(db, org, with_analytics_view=True)
    member.custom_role_id = role.id
    db.commit()

    h = {**headers, "X-Organization-Id": str(org.id)}
    res = client.put(URL, json={"widgets": [{"id": "stats", "visible": True}]}, headers=h)
    assert res.status_code == 200
    assert [w["id"] for w in res.json()["widgets"]] == ["stats"]


def test_malformed_payloads_rejected(client, db):
    headers, user, org = _org_with_user(db, client, "p45-malformed@example.com")
    h = {**headers, "X-Organization-Id": str(org.id)}
    # missing widgets key
    assert client.put(URL, json={}, headers=h).status_code == 422
    # widgets not a list
    assert client.put(URL, json={"widgets": "stats"}, headers=h).status_code == 422
    # entry missing visible is ACCEPTED (visible defaults to true)
    assert client.put(URL, json={"widgets": [{"id": "stats"}]}, headers=h).status_code == 200
    # wrong type for visible (note: pydantic laxly coerces "yes"/"1" to true,
    # which is safe normalization; structured junk is rejected)
    assert client.put(URL, json={"widgets": [{"id": "stats", "visible": {"x": 1}}]}, headers=h).status_code == 422
    assert client.put(URL, json={"widgets": [{"id": "stats", "visible": [True]}]}, headers=h).status_code == 422
    # entry missing id
    assert client.put(URL, json={"widgets": [{"visible": True}]}, headers=h).status_code == 422
    # widget id must be a string (no int coercion)
    assert client.put(URL, json={"widgets": [{"id": 123, "visible": True}]}, headers=h).status_code == 422


def test_layout_size_limit(client, db):
    headers, user, org = _org_with_user(db, client, "p45-limit@example.com")
    h = {**headers, "X-Organization-Id": str(org.id)}
    big = {"widgets": [{"id": "stats", "visible": True} for _ in range(51)]}
    res = client.put(URL, json=big, headers=h)
    assert res.status_code == 422
    # exactly at the limit is accepted (duplicates get collapsed)
    ok = {"widgets": [{"id": "stats", "visible": True} for _ in range(50)]}
    assert client.put(URL, json=ok, headers=h).status_code == 200


def test_non_member_cannot_read_layout(client, db):
    foreign = _register(client, "p45-foreign@example.com")
    _, _, org = _org_with_user(db, client, "p45-owner@example.com")
    res = client.get(URL, headers={**foreign, "X-Organization-Id": str(org.id)})
    assert res.status_code == 403
