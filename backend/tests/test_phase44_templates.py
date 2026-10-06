"""Phase 44 — Project & Workspace Templates.

Covers:
- auth (401), org context, non-member (403), tenant isolation
- project template CRUD (create / list / get / update / archive / delete)
- validation (empty name, unknown ids)
- create project from template (tasks, checklists, labels)
- template/project independence in all directions
- transaction rollback on failure
- duplicate use of a template
- blank project creation still works
"""
import pytest
from uuid import UUID, uuid4


def _uid(value) -> UUID:
    """SA 2.1 requires real UUID objects when binding against Uuid columns."""
    return value if isinstance(value, UUID) else UUID(str(value))

from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.project import Project
from app.models.task import Task, ChecklistItem, Label, TaskLabel
from app.models.project_template import ProjectTemplate, ProjectTemplateTask
from app.schemas.template import ProjectFromTemplateCreate as ProjectFromTemplateCreateSchema

BASE = "/api/v1/templates/project"


def _register(client, email):
    client.post("/api/v1/auth/register", json={"name": "P44 User", "email": email, "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _org_with_user(db, client, email, role=OrganizationRole.OWNER):
    headers = _register(client, email)
    user = db.query(User).filter(User.email == email).first()
    org = Organization(id=uuid4(), name=f"Org {uuid4().hex[:6]}",
                       slug=f"p44-{uuid4().hex[:8]}", created_by=user.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id, role=role))
    db.commit()
    return headers, user, org


def _template(db, org, user, name="Web Kickoff", tasks=None):
    t = ProjectTemplate(id=uuid4(), organization_id=org.id, name=name, created_by_id=user.id)
    db.add(t)
    db.flush()
    for i, task in enumerate(tasks or []):
        db.add(ProjectTemplateTask(
            id=uuid4(), template_id=t.id, position=i,
            title=task["title"],
            description=task.get("description"),
            priority=task.get("priority", "MEDIUM"),
            label_names=task.get("label_names", []),
            checklist_items=task.get("checklist_items", []),
        ))
    db.commit()
    return t


def _create_via_api(client, headers, org, name="API Template", tasks=None):
    payload = {"name": name, "tasks": tasks or []}
    return client.post(BASE, json=payload,
                       headers={**headers, "X-Organization-Id": str(org.id)})


TASKS = [
    {"title": "Setup repo", "checklist_items": ["Create repo", "Add CI"], "label_names": ["infra"]},
    {"title": "Design schema", "priority": "HIGH", "label_names": ["backend"]},
]


# ---------------------------------------------------------------------------
# Auth / org context / RBAC
# ---------------------------------------------------------------------------

def test_unauthenticated_gets_401(client):
    assert client.get(BASE).status_code == 401
    assert client.post(BASE, json={"name": "x"}).status_code == 401


def test_missing_org_header_rejected(client):
    headers = _register(client, "p44-noorg@example.com")
    res = client.get(BASE, headers=headers)
    assert res.status_code in (400, 403)


def test_non_member_gets_403(client, db):
    foreign_headers = _register(client, "p44-foreign@example.com")
    headers, _, org = _org_with_user(db, client, "p44-owner1@example.com")
    res = client.get(BASE, headers={**foreign_headers, "X-Organization-Id": str(org.id)})
    assert res.status_code == 403
    res = client.post(BASE, json={"name": "Sneaky"}, headers={**foreign_headers, "X-Organization-Id": str(org.id)})
    assert res.status_code == 403


def test_foreign_template_id_inaccessible(client, db):
    _, _, org_a = _org_with_user(db, client, "p44-iso-a@example.com")
    user_a = db.query(User).filter(User.email == "p44-iso-a@example.com").first()
    t = _template(db, org_a, user_a)
    headers_b, _, org_b = _org_with_user(db, client, "p44-iso-b@example.com")
    hb = {**headers_b, "X-Organization-Id": str(org_b.id)}
    assert client.get(f"{BASE}/{t.id}", headers=hb).status_code == 404
    assert client.patch(f"{BASE}/{t.id}", json={"name": "Hijacked"}, headers=hb).status_code == 404
    assert client.delete(f"{BASE}/{t.id}", headers=hb).status_code == 404
    # create-project from a foreign template must also be blocked
    res = client.post(f"{BASE}/{t.id}/create-project", json={"name": "Stolen"},
                      headers=hb)
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# CRUD & validation
# ---------------------------------------------------------------------------

def test_template_crud_roundtrip(client, db):
    headers, user, org = _org_with_user(db, client, "p44-crud@example.com")
    h = {**headers, "X-Organization-Id": str(org.id)}

    res = _create_via_api(client, headers, org, tasks=TASKS)
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "API Template"
    assert [t["title"] for t in body["tasks"]] == ["Setup repo", "Design schema"]
    assert body["tasks"][0]["checklist_items"] == ["Create repo", "Add CI"]
    tid = body["id"]

    res = client.get(BASE, headers=h)
    assert res.status_code == 200
    assert any(t["id"] == tid for t in res.json())

    res = client.get(f"{BASE}/{tid}", headers=h)
    assert res.status_code == 200
    assert res.json()["tasks"][1]["priority"] == "HIGH"

    res = client.patch(f"{BASE}/{tid}", json={"name": "Renamed", "tasks": [{"title": "Only task"}]}, headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Renamed"
    assert [t["title"] for t in body["tasks"]] == ["Only task"]

    res = client.delete(f"{BASE}/{tid}", headers=h)
    assert res.status_code == 200
    assert client.get(f"{BASE}/{tid}", headers=h).status_code == 404


def test_template_validation(client, db):
    headers, user, org = _org_with_user(db, client, "p44-valid@example.com")
    res = _create_via_api(client, headers, org, name="   ")
    assert res.status_code == 422
    res = _create_via_api(client, headers, org, name="x" * 200)
    assert res.status_code == 422
    h = {**headers, "X-Organization-Id": str(org.id)}
    assert client.get(f"{BASE}/{uuid4()}", headers=h).status_code == 404


def test_template_archive_and_list_filter(client, db):
    headers, user, org = _org_with_user(db, client, "p44-arch@example.com")
    t = _template(db, org, user, name="To archive")
    h = {**headers, "X-Organization-Id": str(org.id)}
    res = client.post(f"{BASE}/{t.id}/archive", headers=h)
    assert res.status_code == 200
    assert res.json()["is_archived"] is True
    # archived templates hidden from the default list, visible with include_archived
    assert client.get(BASE, headers=h).json() == []
    listed = client.get(BASE, params={"include_archived": "true"}, headers=h).json()
    assert any(x["id"] == str(t.id) for x in listed)


# ---------------------------------------------------------------------------
# Create project from template
# ---------------------------------------------------------------------------

def test_create_project_from_template_copies_content(client, db):
    headers, user, org = _org_with_user(db, client, "p44-apply@example.com")
    db.add(Label(id=uuid4(), organization_id=org.id, name="infra", color="#ff0000"))
    db.commit()
    t = _template(db, org, user, tasks=TASKS)
    h = {**headers, "X-Organization-Id": str(org.id)}

    res = client.post(f"{BASE}/{t.id}/create-project", json={"name": "New Web App"}, headers=h)
    assert res.status_code == 201
    body = res.json()
    assert body["tasks_created"] == 2

    project = db.query(Project).filter(Project.id == _uid(body["project_id"])).first()
    assert project is not None and project.name == "New Web App"
    tasks = db.query(Task).filter(Task.project_id == project.id).order_by(Task.position).all()
    assert [x.title for x in tasks] == ["Setup repo", "Design schema"]
    assert tasks[1].priority.value == "HIGH"

    # checklist copied
    checklists = db.query(ChecklistItem).filter(ChecklistItem.task_id == tasks[0].id).all()
    assert sorted(c.text for c in checklists) == ["Add CI", "Create repo"]

    # labels copied via org label lookup
    label_links = db.query(TaskLabel).filter(TaskLabel.task_id == tasks[0].id).all()
    assert len(label_links) == 1
    label = db.query(Label).filter(Label.id == label_links[0].label_id).first()
    assert label.name == "infra"


def test_unknown_label_name_is_skipped_not_fatal(client, db):
    headers, user, org = _org_with_user(db, client, "p44-label@example.com")
    t = _template(db, org, user, tasks=[{"title": "T", "label_names": ["does-not-exist"]}])
    res = client.post(f"{BASE}/{t.id}/create-project", json={"name": "P"},
                      headers={**headers, "X-Organization-Id": str(org.id)})
    assert res.status_code == 201
    assert res.json()["tasks_created"] == 1


def test_template_independence_both_directions(client, db):
    headers, user, org = _org_with_user(db, client, "p44-indep@example.com")
    t = _template(db, org, user, name="Indep", tasks=[{"title": "Original task", "checklist_items": ["step"]}])
    h = {**headers, "X-Organization-Id": str(org.id)}

    res = client.post(f"{BASE}/{t.id}/create-project", json={"name": "Child"}, headers=h)
    project = db.query(Project).filter(Project.id == _uid(res.json()["project_id"])).first()
    task = db.query(Task).filter(Task.project_id == project.id).first()

    # 1) editing the template afterwards does NOT change the generated project
    client.patch(f"{BASE}/{t.id}", json={"tasks": [{"title": "Changed task"}]}, headers=h)
    db.expire_all()
    assert db.query(Task).filter(Task.id == task.id).first().title == "Original task"

    # 2) deleting the template does NOT touch the project
    client.delete(f"{BASE}/{t.id}", headers=h)
    db.expire_all()
    assert db.query(Task).filter(Task.id == task.id).first() is not None
    assert db.query(Project).filter(Project.id == project.id).first() is not None

    # 3) modifying the generated project does NOT resurrect/alter templates
    task.title = "Locally renamed"
    db.commit()
    assert db.query(ProjectTemplate).filter(ProjectTemplate.id == t.id).first() is None


def test_editing_template_does_not_modify_existing_projects(client, db):
    headers, user, org = _org_with_user(db, client, "p44-edit@example.com")
    t = _template(db, org, user, tasks=[{"title": "Before edit"}])
    h = {**headers, "X-Organization-Id": str(org.id)}
    res = client.post(f"{BASE}/{t.id}/create-project", json={"name": "Frozen"}, headers=h)
    project_id = _uid(res.json()["project_id"])
    client.patch(f"{BASE}/{t.id}", json={"name": "After edit", "tasks": [{"title": "After edit task"}]}, headers=h)
    titles = [x.title for x in db.query(Task).filter(Task.project_id == project_id).all()]
    assert titles == ["Before edit"]


def test_duplicate_project_creation_from_same_template(client, db):
    headers, user, org = _org_with_user(db, client, "p44-dup@example.com")
    t = _template(db, org, user, tasks=[{"title": "Shared"}])
    h = {**headers, "X-Organization-Id": str(org.id)}
    r1 = client.post(f"{BASE}/{t.id}/create-project", json={"name": "Same Name"}, headers=h)
    r2 = client.post(f"{BASE}/{t.id}/create-project", json={"name": "Same Name"}, headers=h)
    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json()["project_id"] != r2.json()["project_id"]
    assert r1.json()["slug"] != r2.json()["slug"]
    # both projects have their own independent task copies
    for pid in (_uid(r1.json()["project_id"]), _uid(r2.json()["project_id"])):
        tasks = db.query(Task).filter(Task.project_id == pid).all()
        assert len(tasks) == 1
        assert tasks[0].task_key.endswith("-1")


def test_archived_template_cannot_spawn_projects(client, db):
    headers, user, org = _org_with_user(db, client, "p44-archapply@example.com")
    t = _template(db, org, user)
    h = {**headers, "X-Organization-Id": str(org.id)}
    client.post(f"{BASE}/{t.id}/archive", headers=h)
    res = client.post(f"{BASE}/{t.id}/create-project", json={"name": "Nope"}, headers=h)
    assert res.status_code == 400


def test_template_task_with_no_project_id_references(client, db):
    """Template tasks must not leak concrete project/task IDs."""
    headers, user, org = _org_with_user(db, client, "p44-noref@example.com")
    t = _template(db, org, user, tasks=TASKS)
    columns = {c.name for c in ProjectTemplateTask.__table__.columns}
    assert "project_id" not in columns and "task_id" not in columns


# ---------------------------------------------------------------------------
# RBAC on project creation from template
# ---------------------------------------------------------------------------

def test_member_role_cannot_create_project_from_template(client, db):
    headers, _, org = _org_with_user(db, client, "p44-mem@example.com", role=OrganizationRole.MEMBER)
    member_user = db.query(User).filter(User.email == "p44-mem@example.com").first()
    t = _template(db, org, member_user)
    res = client.post(f"{BASE}/{t.id}/create-project", json={"name": "Forbidden"},
                      headers={**headers, "X-Organization-Id": str(org.id)})
    assert res.status_code == 403
    # but members can still read templates and do template CRUD
    assert client.get(BASE, headers={**headers, "X-Organization-Id": str(org.id)}).status_code == 200


def test_no_cross_tenant_task_leakage(client, db):
    _, user_a, org_a = _org_with_user(db, client, "p44-leak-a@example.com")
    t = _template(db, org_a, user_a, tasks=[{"title": "Secret Task"}])
    headers_b, _, org_b = _org_with_user(db, client, "p44-leak-b@example.com")
    res = client.post(f"{BASE}/{t.id}/create-project", json={"name": "Evil"},
                      headers={**headers_b, "X-Organization-Id": str(org_b.id)})
    assert res.status_code == 404
    assert db.query(Task).filter(Task.title == "Evil").count() == 0
    assert db.query(Task).filter(Task.title == "Secret Task").count() == 0


# ---------------------------------------------------------------------------
# Rollback / failure handling
# ---------------------------------------------------------------------------

def test_failed_project_creation_rolls_back(monkeypatch):
    """If task creation fails mid-way, no project or task rows may survive.

    Tested against a standalone session so the rollback semantics are verified
    without the shared-test-transaction fixture getting in the way.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    from app.db.base import Base
    from app.api.v1 import templates as tm

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    user = User(id=uuid4(), name="Rollback User", email="rb@example.com", password_hash="x")
    org = Organization(id=uuid4(), name="RB Org", slug=f"rb-{uuid4().hex[:8]}", created_by=user.id)
    session.add_all([user, org])
    session.flush()
    session.add(OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id, role=OrganizationRole.OWNER))
    t = _template(session, org, user, tasks=TASKS)

    real_flush = Session.flush

    def exploding_flush(self, *a, **kw):
        # let the project row flush, then blow up on the first task insert
        if any(isinstance(o, Task) for o in self.new):
            raise RuntimeError("boom")
        return real_flush(self, *a, **kw)

    monkeypatch.setattr(Session, "flush", exploding_flush)
    with pytest.raises(RuntimeError, match="boom"):
        tm.create_project_from_template(
            db=session,
            org_id=org.id,
            template_id=t.id,
            project_in=ProjectFromTemplateCreateSchema(name="Doomed"),
            current_user=user,
        )
    monkeypatch.undo()

    # nothing partially created
    assert session.query(Project).filter(Project.name == "Doomed").count() == 0
    assert session.query(Task).filter(Task.title == "Setup repo").count() == 0
    # template untouched and reusable after the failure
    assert session.query(ProjectTemplateTask).filter(ProjectTemplateTask.template_id == t.id).count() == len(TASKS)
    retry = tm.create_project_from_template(
        db=session,
        org_id=org.id,
        template_id=t.id,
        project_in=ProjectFromTemplateCreateSchema(name="Doomed"),
        current_user=user,
    )
    assert retry.tasks_created == len(TASKS)
    assert session.query(Project).filter(Project.name == "Doomed").count() == 1


# ---------------------------------------------------------------------------
# Blank project creation still works
# ---------------------------------------------------------------------------

def test_blank_project_creation_still_works(client, db):
    headers, _, org = _org_with_user(db, client, "p44-blank@example.com")
    res = client.post("/api/v1/projects", json={"name": "Plain Project"},
                      headers={**headers, "X-Organization-Id": str(org.id)})
    assert res.status_code == 201
    assert res.json()["name"] == "Plain Project"
    # and no tasks exist
    project = db.query(Project).filter(Project.id == _uid(res.json()["id"])).first()
    assert db.query(Task).filter(Task.project_id == project.id).count() == 0
