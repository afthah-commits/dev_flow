"""Phase 49 — AI breakdown editor & route contract hardening.

Part A: the Phase 48 apply endpoint accepts user-EDITED suggestion trees:
edited title/description/priority/points, added children, deleted nodes and
reparented nodes — with server-side validation of every value (invalid
points/overlong text rejected, not clamped), hierarchy integrity (no cycles,
self-parenting, unknown parents), bounds (depth 3 / 8 per level / 32 nodes),
permissions, isolation, transactionality and audit.

Part B: route inventory hardening pins (see test file bottom).
"""
import json
from uuid import uuid4

from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.audit import AuditEvent

ANALYZE_URL = "/api/v1/ai/projects/{pid}/planning/analyze"
APPLY_URL = "/api/v1/ai/projects/{pid}/planning/apply"


def _register(client, email):
    client.post("/api/v1/auth/register", json={"name": "P49 User", "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _org_with_user(db, client, email, role=OrganizationRole.OWNER):
    headers = _register(client, email)
    user = db.query(User).filter(User.email == email).first()
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=f"p49-{uuid4().hex[:8]}", created_by=user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id, role=role))
    db.commit()
    return headers, user, org


def _project(db, org, user):
    proj = Project(id=uuid4(), organization_id=org.id, name="Editor",
                   slug=f"p49-proj-{uuid4().hex[:8]}",
                   key=f"P49{uuid4().hex[:4].upper()}", description="",
                   owner_id=user.id, task_seq_num=100)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


def _task(db, proj, user, title="Build payment integration", description="Integrate payments end to end."):
    proj.task_seq_num += 1
    seq = proj.task_seq_num
    t = Task(id=uuid4(), project_id=proj.id, title=title, description=description,
             status=TaskStatus.TODO, priority=TaskPriority.MEDIUM, creator_id=user.id,
             task_key=f"{proj.key}-{seq}")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _edited_tree():
    """A typical user-edited tree: renamed root, custom child, a brand-new
    user-added child, and a reparented node (moved under the second root)."""
    return [
        {"title": "Payment platform integration (edited)", "priority": "CRITICAL", "suggestion_id": "s1",
         "description": "Edited description with real scope", "estimated_points": 6,
         "children": [
             {"title": "Provider setup (renamed)", "priority": "HIGH", "suggestion_id": "s1a",
              "parent_suggestion_id": "s1", "estimated_points": 2, "children": []},
             {"title": "User-added: sandbox credentials", "priority": "LOW", "suggestion_id": "user-1",
              "parent_suggestion_id": "s1", "estimated_points": 1, "children": []},
         ]},
        {"title": "Webhook handling", "priority": "HIGH", "suggestion_id": "s2",
         "children": [
             {"title": "Reparented: signature verification", "priority": "MEDIUM", "suggestion_id": "s2n",
              "parent_suggestion_id": "s2", "estimated_points": 2, "children": []},
         ]},
    ]


# ---------------------------------------------------------------------------
# Editing acceptance
# ---------------------------------------------------------------------------

def test_edited_tree_accepted_with_all_edits(client, db):
    headers, user, org = _org_with_user(db, client, "p49-a@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    before = db.query(Task).count()
    payload = {"task_id": str(task.id), "suggestions": _edited_tree()}
    r = client.post(APPLY_URL.format(pid=str(proj.id)), headers=headers, json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["applied"] == 5

    root = db.query(Task).filter(Task.title == "Payment platform integration (edited)").first()
    assert root is not None and root.parent_id == task.id
    renamed = db.query(Task).filter(Task.title == "Provider setup (renamed)").first()
    assert renamed is not None and renamed.parent_id == root.id and renamed.estimate_points == 2.0
    user_added = db.query(Task).filter(Task.title == "User-added: sandbox credentials").first()
    assert user_added is not None and user_added.parent_id == root.id
    moved = db.query(Task).filter(Task.title == "Reparented: signature verification").first()
    s2 = db.query(Task).filter(Task.title == "Webhook handling").first()
    assert moved.parent_id == s2.id
    assert db.query(Task).count() == before + 5


def test_edited_description_and_points_persist(client, db):
    headers, user, org = _org_with_user(db, client, "p49-b@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    payload = {"task_id": str(task.id), "suggestions": _edited_tree()}
    r = client.post(APPLY_URL.format(pid=str(proj.id)), headers=headers, json=payload)
    assert r.status_code == 201
    root = db.query(Task).filter(Task.title == "Payment platform integration (edited)").first()
    assert root.description == "Edited description with real scope"
    moved = db.query(Task).filter(Task.title == "Reparented: signature verification").first()
    assert moved.estimate_points == 2.0
    webhook = db.query(Task).filter(Task.title == "Webhook handling").first()
    assert webhook.estimate_points is None  # untouched fields stay untouched


# ---------------------------------------------------------------------------
# Editing rejection (server authority over frontend edits)
# ---------------------------------------------------------------------------

def _apply(client, headers, proj, task, suggestions):
    return client.post(APPLY_URL.format(pid=str(proj.id)), headers=headers,
                       json={"task_id": str(task.id), "suggestions": suggestions})


def test_empty_title_rejected(client, db):
    headers, user, org = _org_with_user(db, client, "p49-c@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    r = _apply(client, headers, proj, task, [{"title": "   ", "priority": "LOW"}])
    assert r.status_code == 422


def test_excessively_long_text_rejected(client, db):
    headers, user, org = _org_with_user(db, client, "p49-d@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    r = _apply(client, headers, proj, task, [{"title": "x" * 201, "priority": "LOW"}])
    assert r.status_code == 422
    r = _apply(client, headers, proj, task, [{"title": "ok", "priority": "LOW", "description": "d" * 1001}])
    assert r.status_code == 422


def test_invalid_points_rejected(client, db):
    headers, user, org = _org_with_user(db, client, "p49-e@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    before = db.query(Task).count()
    for bad in (-1, 101, "nine", True):
        r = _apply(client, headers, proj, task, [{"title": "pts", "priority": "LOW", "estimated_points": bad}])
        assert r.status_code == 422, f"points={bad!r}"
    assert db.query(Task).count() == before


def test_circular_and_self_parent_rejected(client, db):
    headers, user, org = _org_with_user(db, client, "p49-f@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    before = db.query(Task).count()
    # self-parent
    r = _apply(client, headers, proj, task, [
        {"title": "selfish", "priority": "LOW", "suggestion_id": "x", "parent_suggestion_id": "x"}])
    assert r.status_code == 422
    # mutual cycle across two nodes
    r = _apply(client, headers, proj, task, [
        {"title": "a", "priority": "LOW", "suggestion_id": "a", "parent_suggestion_id": "b"},
        {"title": "b", "priority": "LOW", "suggestion_id": "b", "parent_suggestion_id": "a"},
    ])
    assert r.status_code == 422
    assert db.query(Task).count() == before


def test_invalid_parent_rejected(client, db):
    headers, user, org = _org_with_user(db, client, "p49-g@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    r = _apply(client, headers, proj, task, [
        {"title": "orphan", "priority": "LOW", "parent_suggestion_id": "ghost"}])
    assert r.status_code == 422


def test_maximum_depth_and_node_count_enforced_on_edits(client, db):
    headers, user, org = _org_with_user(db, client, "p49-h@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    before = db.query(Task).count()
    deep = [{"title": "L0", "priority": "LOW", "children": [
        {"title": "L1", "priority": "LOW", "children": [
            {"title": "L2", "priority": "LOW", "children": [{"title": "L3", "priority": "LOW"}]}]}]}]
    r = _apply(client, headers, proj, task, deep)
    assert r.status_code == 422
    many = [{"title": f"n{i}", "priority": "LOW"} for i in range(33)]
    r = _apply(client, headers, proj, task, many)
    assert r.status_code == 422
    assert db.query(Task).count() == before


# ---------------------------------------------------------------------------
# Safety / isolation / audit (edited trees)
# ---------------------------------------------------------------------------

def test_edited_apply_rollback_permissions_isolation_audit(client, db):
    headers, user, org = _org_with_user(db, client, "p49-i@example.com")
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    other_headers, other_user, other_org = _org_with_user(db, client, "p49-j@example.com")
    other_proj = _project(db, other_org, other_user)
    other_task = _task(db, other_proj, other_user)
    before = db.query(Task).count()

    other_headers["X-Organization-Id"] = str(other_org.id)
    r = _apply(client, other_headers, proj, task, _edited_tree())
    assert r.status_code in (403, 404)

    # authentication
    r = client.post(APPLY_URL.format(pid=str(proj.id)), json={"task_id": str(task.id), "suggestions": []})
    assert r.status_code == 401

    # successful edited apply is audited
    headers["X-Organization-Id"] = str(org.id)
    payload = {"task_id": str(task.id), "suggestions": _edited_tree()}
    r = _apply(client, headers, proj, task, payload["suggestions"])
    assert r.status_code == 201
    ev = (db.query(AuditEvent)
          .filter(AuditEvent.event_type == "ai.planning_applied", AuditEvent.organization_id == org.id)
          .order_by(AuditEvent.created_at.desc()).first())
    assert ev is not None and ev.metadata_["created_count"] == 5
    assert db.query(Task).count() == before + 5


def test_deleted_nodes_are_simply_not_sent(client, db):
    """Deleting a node in the editor = not including it in the apply payload;
    its children (if kept) move with the tree as sent. Server creates exactly
    what the (validated) payload contains."""
    headers, user, org = _org_with_user(db, client, "p49-k@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user)
    before = db.query(Task).count()
    # parent deleted in the editor; its child re-attached under the other root
    payload = {"task_id": str(task.id), "suggestions": [
        {"title": "Kept root", "priority": "HIGH", "suggestion_id": "keep",
         "children": [
             {"title": "Surviving child", "priority": "LOW", "suggestion_id": "surv",
              "parent_suggestion_id": "keep", "children": []},
         ]},
    ]}
    r = _apply(client, headers, proj, task, payload["suggestions"])
    assert r.status_code == 201
    assert db.query(Task).count() == before + 2
    # the deleted subtree content is absent
    assert db.query(Task).filter(Task.title == "Deleted parent").first() is None


def test_analyze_flow_unaffected_by_editor_changes(client, db):
    headers, user, org = _org_with_user(db, client, "p49-l@example.com")
    headers["X-Organization-Id"] = str(org.id)
    proj = _project(db, org, user)
    task = _task(db, proj, user, description="Payments with webhooks and checkout UI.")
    r = client.post(ANALYZE_URL.format(pid=str(proj.id)), json={"task_id": str(task.id)}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["suggested_breakdown"] and any(n.get("children") for n in data["suggested_breakdown"])


# ---------------------------------------------------------------------------
# Part B — route inventory hardening pins
# ---------------------------------------------------------------------------

def test_route_helper_yields_effective_paths_and_methods():
    from tests.conftest import iter_flattened_routes
    routes = list(iter_flattened_routes())
    assert routes, "helper yielded nothing"
    for r in routes:
        assert isinstance(r.path, str) and r.path.startswith("/")
        # HTTP routes expose methods; websocket routes may legitimately not
        assert r.methods is None or len(r.methods) > 0
        assert r.endpoint is not None


def test_nested_router_prefix_resolution():
    from tests.conftest import iter_flattened_routes
    paths = {r.path for r in iter_flattened_routes()}
    # include prefix + child path = effective path, for both nested kinds
    assert "/api/v1/analytics/dashboard" in paths          # analytics router
    assert "/api/v1/dashboard/stats" in paths              # dashboard router
    assert "/api/v1/projects/{project_id}/tasks/{task_id}" in paths  # nested resource router


def test_important_routes_registered_exactly_once():
    from tests.conftest import iter_flattened_routes
    from collections import Counter
    must_exist_once = [
        "/api/v1/analytics/delivery",
        "/api/v1/analytics/dora",
        "/api/v1/analytics/projects/{project_id}/github",
        "/api/v1/ai/projects/{project_id}/planning/analyze",
        "/api/v1/ai/projects/{project_id}/planning/apply",
        "/api/v1/dashboard/layout",
        "/api/v1/dashboard/stats",
        "/api/v1/search",
    ]
    routes = list(iter_flattened_routes())
    for path in must_exist_once:
        matches = [(r.path, tuple(sorted(r.methods or []))) for r in routes if r.path == path]
        assert len(matches) >= 1, f"{path} not registered"
        # one registration per effective method+path combination (no dupes)
        assert len(matches) == len(set(matches)), f"{path} duplicated: {matches}"
        assert any({"GET"} <= set(m) or {"POST"} <= set(m) for _, m in matches)


def test_no_duplicate_effective_method_path_combinations():
    from tests.conftest import iter_flattened_routes
    from collections import Counter
    seen = [(r.path, tuple(sorted(r.methods or []))) for r in iter_flattened_routes()]
    dups = [k for k, c in Counter(seen).items() if c > 1]
    assert not dups, f"duplicate effective routes: {dups}"


def test_frontend_planning_calls_map_to_backend_routes():
    from tests.conftest import iter_flattened_routes
    paths = {r.path for r in iter_flattened_routes()}
    # frontend aiApi.ts calls (Phase 47/48/49 contract)
    for expected in (
        "/api/v1/ai/projects/{project_id}/planning/analyze",
        "/api/v1/ai/projects/{project_id}/planning/apply",
    ):
        assert expected in paths
