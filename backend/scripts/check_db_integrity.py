#!/usr/bin/env python3
"""Phase 31 — database integrity checker (REPORT ONLY).

Scans the configured database for orphaned records, broken foreign keys,
duplicate memberships, invalid state values and cross-entity inconsistencies.
It NEVER deletes or modifies data — it only reports what it finds.

Usage:
    cd backend
    python scripts/check_db_integrity.py                 # check configured DB
    python scripts/check_db_integrity.py sqlite:///./devflow.db

Exit codes: 0 = no issues, 1 = issues found, 2 = execution error.
Works with SQLite and PostgreSQL (UUID values are normalized before compare).
"""
import os
import re
import sys
from uuid import UUID

# Allow running as `python scripts/check_db_integrity.py` from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def mask_url(url: str) -> str:
    """Hide credentials before printing a database URL."""
    return re.sub(r"//([^:/@]+)(:[^@]*)?@", r"//\1:***@", url)


def norm(value) -> str | None:
    """Normalize any UUID-ish value to a canonical hex form."""
    if value is None:
        return None
    try:
        return UUID(str(value)).hex
    except (ValueError, AttributeError, TypeError):
        return str(value).lower().replace("-", "")


def fetch_id_set(conn, sql: str) -> set[str]:
    return {norm(r[0]) for r in conn.execute(text(sql))}


def check_orphans(conn, issues: list, label: str,
                  child_sql: str, parent_ids: set[str], ref_col: str = "ref"):
    """Report child rows whose reference is missing from the parent id set."""
    orphans = []
    for row in conn.execute(text(child_sql)):
        child_id, ref = row[0], row[1]
        if ref is not None and norm(ref) not in parent_ids:
            orphans.append((str(child_id), str(ref)))
    if orphans:
        samples = ", ".join(f"{c}->{r}" for c, r in orphans[:5])
        more = f" (+{len(orphans) - 5} more)" if len(orphans) > 5 else ""
        issues.append(f"{label}: {len(orphans)} orphaned row(s) [{samples}]{more}")


def check_duplicates(conn, issues: list, label: str, sql: str):
    rows = conn.execute(text(sql)).fetchall()
    if rows:
        samples = ", ".join(str(tuple(r)) for r in rows[:5])
        issues.append(f"{label}: {len(rows)} duplicate group(s) [{samples}]")


def check_invalid_values(conn, issues: list, label: str, sql: str):
    rows = conn.execute(text(sql)).fetchall()
    if rows:
        samples = ", ".join(str(tuple(r)) for r in rows[:5])
        issues.append(f"{label}: {len(rows)} invalid value(s) [{samples}]")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def run_checks(engine) -> list[str]:
    issues: list[str] = []
    with engine.connect() as conn:
        dialect = engine.dialect.name

        # -- 0. SQLite built-in foreign key check (schema-declared FKs) -----
        if dialect == "sqlite":
            rows = conn.execute(text("PRAGMA foreign_key_check")).fetchall()
            if rows:
                samples = ", ".join(f"table={r[0]} rowid={r[1]}" for r in rows[:5])
                more = f" (+{len(rows) - 5} more)" if len(rows) > 5 else ""
                issues.append(f"FK check (PRAGMA foreign_key_check): {len(rows)} violation(s) [{samples}]{more}")

        # -- id sets -------------------------------------------------------
        users = fetch_id_set(conn, "SELECT id FROM users")
        orgs = fetch_id_set(conn, "SELECT id FROM organizations")
        projects = fetch_id_set(conn, "SELECT id FROM projects")
        tasks = fetch_id_set(conn, "SELECT id FROM tasks")
        states = fetch_id_set(conn, "SELECT id FROM workflow_states")
        workflows = fetch_id_set(conn, "SELECT id FROM workflows")
        clients = fetch_id_set(conn, "SELECT id FROM clients")
        sprints = fetch_id_set(conn, "SELECT id FROM sprints")

        # -- 1. orphaned records / broken foreign keys ---------------------
        check_orphans(conn, issues, "tasks -> projects",
                      "SELECT id, project_id FROM tasks WHERE project_id IS NOT NULL", projects)
        check_orphans(conn, issues, "tasks -> users (reporter/assignee)",
                      "SELECT id, assignee_id FROM tasks WHERE assignee_id IS NOT NULL", users)
        check_orphans(conn, issues, "tasks -> tasks (parent)",
                      "SELECT id, parent_id FROM tasks WHERE parent_id IS NOT NULL", tasks)
        check_orphans(conn, issues, "sprints -> projects",
                      "SELECT id, project_id FROM sprints WHERE project_id IS NOT NULL", projects)
        check_orphans(conn, issues, "projects -> organizations",
                      "SELECT id, organization_id FROM projects WHERE organization_id IS NOT NULL", orgs)
        check_orphans(conn, issues, "organization_members -> organizations",
                      "SELECT id, organization_id FROM organization_members WHERE organization_id IS NOT NULL", orgs)
        check_orphans(conn, issues, "organization_members -> users",
                      "SELECT id, user_id FROM organization_members WHERE user_id IS NOT NULL", users)
        check_orphans(conn, issues, "time_entries -> tasks",
                      "SELECT id, task_id FROM time_entries WHERE task_id IS NOT NULL", tasks)
        check_orphans(conn, issues, "active_timers -> projects",
                      "SELECT id, project_id FROM active_timers WHERE project_id IS NOT NULL", projects)
        check_orphans(conn, issues, "notifications -> users",
                      "SELECT id, user_id FROM notifications WHERE user_id IS NOT NULL", users)
        check_orphans(conn, issues, "workflows -> organizations",
                      "SELECT id, organization_id FROM workflows WHERE organization_id IS NOT NULL", orgs)
        check_orphans(conn, issues, "workflow_states -> workflows",
                      "SELECT id, workflow_id FROM workflow_states WHERE workflow_id IS NOT NULL", workflows)
        check_orphans(conn, issues, "workflow_versions -> workflows",
                      "SELECT id, workflow_id FROM workflow_versions WHERE workflow_id IS NOT NULL", workflows)
        check_orphans(conn, issues, "workflow_state_layouts -> workflow_states",
                      "SELECT id, state_id FROM workflow_state_layouts WHERE state_id IS NOT NULL", states)
        check_orphans(conn, issues, "jobs -> organizations",
                      "SELECT id, organization_id FROM jobs WHERE organization_id IS NOT NULL", orgs)
        check_orphans(conn, issues, "deployments -> projects",
                      "SELECT id, project_id FROM deployments WHERE project_id IS NOT NULL", projects)
        check_orphans(conn, issues, "automations -> organizations",
                      "SELECT id, organization_id FROM automations WHERE organization_id IS NOT NULL", orgs)
        check_orphans(conn, issues, "api_keys -> organizations",
                      "SELECT id, organization_id FROM api_keys WHERE organization_id IS NOT NULL", orgs)
        check_orphans(conn, issues, "webhook_endpoints -> organizations",
                      "SELECT id, organization_id FROM webhook_endpoints WHERE organization_id IS NOT NULL", orgs)
        check_orphans(conn, issues, "clients -> organizations",
                      "SELECT id, organization_id FROM clients WHERE organization_id IS NOT NULL", orgs)
        check_orphans(conn, issues, "client_project_access -> clients",
                      "SELECT id, client_id FROM client_project_access WHERE client_id IS NOT NULL", clients)
        check_orphans(conn, issues, "client_project_access -> projects",
                      "SELECT id, project_id FROM client_project_access WHERE project_id IS NOT NULL", projects)

        # -- 2. broken workflow transitions -------------------------------
        # from/to states must exist AND belong to the transition's workflow
        rows = conn.execute(text(
            "SELECT id, workflow_id, from_state_id, to_state_id FROM workflow_transitions"
        )).fetchall()
        state_owner = {
            norm(r[0]): norm(r[1])
            for r in conn.execute(text("SELECT id, workflow_id FROM workflow_states"))
        }
        broken = []
        for tid, wf, src, dst in rows:
            wf_n = norm(wf)
            for st in (src, dst):
                if st is None:
                    continue
                st_n = norm(st)
                if st_n not in states:
                    broken.append(f"{tid}: state {st} missing")
                elif st_n in state_owner and state_owner[st_n] != wf_n:
                    broken.append(f"{tid}: state {st} belongs to another workflow")
        if broken:
            samples = "; ".join(broken[:5])
            more = f" (+{len(broken) - 5} more)" if len(broken) > 5 else ""
            issues.append(f"workflow_transitions: {len(broken)} broken link(s) [{samples}]{more}")

        # -- 3. invalid workflow versions ---------------------------------
        check_duplicates(conn, issues, "workflow_versions duplicate version_number",
                          "SELECT workflow_id, version_number, COUNT(*) FROM workflow_versions "
                          "GROUP BY workflow_id, version_number HAVING COUNT(*) > 1")
        check_invalid_values(conn, issues, "workflow_versions PUBLISHED without snapshot",
                             "SELECT id, workflow_id FROM workflow_versions "
                             "WHERE status = 'PUBLISHED' AND snapshot IS NULL")

        # -- 4. duplicate organization memberships -------------------------
        check_duplicates(conn, issues, "duplicate organization memberships",
                          "SELECT organization_id, user_id, COUNT(*) FROM organization_members "
                          "GROUP BY organization_id, user_id HAVING COUNT(*) > 1")

        # -- 5. invalid project ownership (owner not in the org) -----------
        rows = conn.execute(text(
            "SELECT p.id, p.owner_id, p.organization_id FROM projects p "
            "WHERE p.owner_id IS NOT NULL"
        )).fetchall()
        member_pairs = {
            (norm(r[0]), norm(r[1]))
            for r in conn.execute(text("SELECT organization_id, user_id FROM organization_members"))
        }
        bad_owners = [str(pid) for pid, owner, org in rows
                      if (norm(org), norm(owner)) not in member_pairs]
        if bad_owners:
            samples = ", ".join(bad_owners[:5])
            more = f" (+{len(bad_owners) - 5} more)" if len(bad_owners) > 5 else ""
            issues.append(f"invalid project ownership: {len(bad_owners)} project(s) whose owner is not "
                          f"a member of the project's organization [{samples}]{more}")

        # -- 6. invalid task relationships (parent in a different project) --
        rows = conn.execute(text(
            "SELECT id, parent_id, project_id FROM tasks WHERE parent_id IS NOT NULL"
        )).fetchall()
        task_project = {norm(r[0]): norm(r[1]) for r in
                        conn.execute(text("SELECT id, project_id FROM tasks"))}
        cross = [str(tid) for tid, parent, proj in rows
                 if task_project.get(norm(parent)) is not None
                 and task_project.get(norm(parent)) != norm(proj)]
        if cross:
            samples = ", ".join(cross[:5])
            more = f" (+{len(cross) - 5} more)" if len(cross) > 5 else ""
            issues.append(f"invalid task relationships: {len(cross)} task(s) whose parent belongs "
                          f"to a different project [{samples}]{more}")

        # -- 7. duplicate active timers ------------------------------------
        check_duplicates(conn, issues, "duplicate active timers",
                          "SELECT organization_id, user_id, COUNT(*) FROM active_timers "
                          "GROUP BY organization_id, user_id HAVING COUNT(*) > 1")

        # -- 8. duplicate idempotency keys ---------------------------------
        check_duplicates(conn, issues, "duplicate idempotency keys",
                          "SELECT idempotency_key, COUNT(*) FROM jobs "
                          "WHERE idempotency_key IS NOT NULL "
                          "GROUP BY idempotency_key HAVING COUNT(*) > 1")

        # -- 9. invalid job states -----------------------------------------
        check_invalid_values(conn, issues, "invalid job states",
                             "SELECT id, status FROM jobs WHERE status NOT IN "
                             "('QUEUED', 'RUNNING', 'SUCCESS', 'FAILED', 'RETRYING', 'CANCELLED')")

        # -- 10. invalid deployment states ---------------------------------
        check_invalid_values(conn, issues, "invalid deployment states",
                             "SELECT id, status FROM deployments WHERE status NOT IN "
                             "('QUEUED', 'BUILDING', 'DEPLOYING', 'RUNNING', 'SUCCESS', "
                             "'FAILED', 'CANCELLED', 'ROLLED_BACK')")

        # -- 11. invalid client access records -----------------------------
        check_invalid_values(conn, issues, "invalid client access level",
                             "SELECT id, access_level FROM client_project_access WHERE access_level "
                             "NOT IN ('READ', 'COMMENT', 'WRITE', 'ADMIN')")
        check_invalid_values(conn, issues, "invalid client request status",
                             "SELECT id, status FROM client_requests WHERE status NOT IN "
                             "('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')")

    return issues


def main() -> int:
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        from app.core.config import settings
        url = settings.DATABASE_URL

    print(f"Database: {mask_url(url)}")
    print("Mode: REPORT ONLY (no data is modified)\n")

    try:
        engine = create_engine(url)
        issues = run_checks(engine)
    except Exception as exc:  # pragma: no cover - operator tooling
        print(f"ERROR: {type(exc).__name__}: {exc}")
        return 2

    if issues:
        print(f"FOUND {len(issues)} issue group(s):\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print("\nResult: ISSUES DETECTED (nothing was modified)")
        return 1

    print("Result: ALL CHECKS PASSED — no integrity issues detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
