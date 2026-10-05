#!/usr/bin/env python3
"""Phase 31 — API query-count probe.

Boots the app against a throwaway SQLite database, seeds representative data,
then measures SQL statement counts per high-traffic endpoint to expose N+1
patterns. Read-only with respect to your real database (uses its own file).

Usage:
    cd backend
    python scripts/perf_probe.py

Interpretation: SELECT counts that scale with list size (e.g. ~3 queries per
row) indicate N+1 access; constant counts indicate set-based SQL.
"""
import os
import sys
import uuid
import time

# Must be set before app imports (settings are read at import time)
PROBE_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "perf_probe.db")
if os.path.exists(PROBE_DB):
    os.remove(PROBE_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{PROBE_DB}"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import event  # noqa: E402

from app.db.session import engine, SessionLocal  # noqa: E402
from app.db.base import Base  # noqa: E402

# --- query counter ---------------------------------------------------------
counts = {"n": 0, "select": 0}


def _before(conn, cursor, statement, parameters, context, executemany):
    counts["n"] += 1
    if statement.lstrip().upper().startswith("SELECT"):
        counts["select"] += 1


event.listen(engine, "before_cursor_execute", _before)


def reset():
    counts["n"] = 0
    counts["select"] = 0


# --- setup -----------------------------------------------------------------
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.project import Project  # noqa: E402
from app.models.task import Task, TaskStatus  # noqa: E402
from app.models.sprint import Sprint, SprintStatus  # noqa: E402

Base.metadata.create_all(bind=engine)
client = TestClient(app)

email = f"perf_{uuid.uuid4().hex[:8]}@probe.com"
client.post("/api/v1/auth/register", json={"name": "Perf", "email": email, "password": "password123"})
token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
auth = {"Authorization": f"Bearer {token}"}
org = client.post("/api/v1/organizations", json={"name": "Perf Org"}, headers=auth).json()
headers = {**auth, "X-Organization-Id": org["id"]}

db = SessionLocal()
user = db.query(User).filter(User.email == email).first()

# Seed: 3 projects x 10 tasks, 2 active sprints, 1 workflow with states
projects = []
for p in range(3):
    proj = Project(
        id=uuid.uuid4(), name=f"Perf Project {p}", slug=f"perf-{p}-{uuid.uuid4().hex[:6]}",
        organization_id=uuid.UUID(str(org["id"])), owner_id=user.id,
    )
    db.add(proj)
    projects.append(proj)
db.flush()

for proj in projects:
    for t in range(10):
        db.add(Task(
            id=uuid.uuid4(), project_id=proj.id, title=f"Task {t}",
            status=TaskStatus.DONE if t % 2 == 0 else TaskStatus.TODO,
            priority="MEDIUM", creator_id=user.id,
            estimate_points=3,
        ))

for s in range(2):
    sprint = Sprint(
        id=uuid.uuid4(), project_id=projects[0].id, key=f"PERF-S{s}-{uuid.uuid4().hex[:4]}",
        name=f"Perf Sprint {s}", status=SprintStatus.ACTIVE,
    )
    db.add(sprint)
    db.flush()
    for t in range(5):
        db.add(Task(
            id=uuid.uuid4(), project_id=projects[0].id, sprint_id=sprint.id,
            title=f"Sprint Task {s}-{t}",
            status=TaskStatus.DONE if t % 2 == 0 else TaskStatus.TODO,
            priority="MEDIUM", creator_id=user.id, estimate_points=5,
        ))
db.commit()

# Workflow via API (states + transition) so analytics has data
wf = client.post("/api/v1/workflows",
                 json={"name": "Perf WF", "entity_type": "TASK", "states": [], "transitions": []},
                 headers=headers).json()
todo = client.post(f"/api/v1/workflows/{wf['id']}/states",
                   json={"name": "To Do", "key": "TODO", "is_initial": True}, headers=headers).json()
done = client.post(f"/api/v1/workflows/{wf['id']}/states",
                   json={"name": "Done", "key": "DONE", "is_terminal": True}, headers=headers).json()
client.post(f"/api/v1/workflows/{wf['id']}/transitions",
            json={"name": "Finish", "from_state_id": todo["id"], "to_state_id": done["id"]},
            headers=headers)
db.expire_all()

# --- endpoints -------------------------------------------------------------
ENDPOINTS = [
    ("GET", "/api/v1/dashboard/stats", None),
    ("GET", "/api/v1/dashboard/sprints/active", None),
    ("GET", f"/api/v1/projects", {"organization_id": org["id"]}),
    ("GET", f"/api/v1/projects/{projects[0].id}/tasks", None),
    ("GET", "/api/v1/notifications", None),
    ("GET", "/api/v1/workflows", None),
    ("GET", "/api/v1/jobs", None),
    ("GET", "/api/v1/knowledge/documents", None),
    ("GET", "/api/v1/reports/", None),
    ("GET", "/api/v1/analytics/dashboard", None),
    ("GET", "/api/v1/dashboards/", None),
    ("GET", f"/api/v1/automations?organization_id={org['id']}", None),
    ("GET", f"/api/v1/workflows/{wf['id']}/analytics", None),
]

print(f"{'endpoint':<55} {'status':>6} {'selects':>8} {'total':>6} {'ms':>7}")
print("-" * 86)
worst = []
for method, url, params in ENDPOINTS:
    reset()
    start = time.perf_counter()
    res = client.get(url, headers=headers, params=params)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"{url[:55]:<55} {res.status_code:>6} {counts['select']:>8} {counts['n']:>6} {elapsed:>7.1f}")
    if res.status_code != 200:
        print(f"    -> {res.text[:160]}")
    if counts["select"] > 20:
        worst.append((url, counts["select"]))

print("-" * 86)
if worst:
    print("N+1 SUSPECTS (selects > 20):")
    for url, n in worst:
        print(f"  {url}: {n} SELECTs")
else:
    print("No endpoint exceeded 20 SELECTs.")

db.close()
try:
    os.remove(PROBE_DB)
except OSError:
    pass
