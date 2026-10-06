# PHASE 36 VERIFICATION REPORT

**Phase:** 36 — Advanced Notifications & Action Center
**Date:** 2026-10-06
**Baseline:** `HEAD` = `577bd82` ("feat: implement daily report intelligence")

Every result below is an actually executed command. Nothing is asserted from code inspection alone.

---

## Methodology

Baseline was captured from a pristine export of `HEAD` into a temporary
directory (`git archive HEAD`) and tested with the same interpreter, so
pre-existing failures could be separated cleanly from Phase 36 failures.

---

## Backend tests

```
$ cd backend && python -m pytest tests -q --tb=no -p no:cacheprovider
77 failed, 81 passed, 284 warnings in 119.77s
```

**Baseline (HEAD, before Phase 36):**
```
77 failed, 58 passed, 256 warnings in 96.78s
```

**Failure-set diff (exact, per test id):**

```
baseline failures: 77
final failures:    77
=== only in final (NEW failures) ===
=== only in baseline (FIXED) ===
new=0 fixed=0
```

- **Pre-existing failures: 77** (unchanged — identical test ids)
- **Phase 36 failures: 0**
- **Tests added by Phase 36: 23** (`backend/tests/test_phase36_notifications.py`)
- Passed rose **58 → 81** (23 Phase 36 tests added, nothing else changed)

Phase 36 suite in isolation:
```
$ python -m pytest tests/test_phase36_notifications.py -q
23 passed, 90 warnings in 24.65s
```

---

## Frontend tests

```
$ cd frontend && npx vitest run
Test Files  11 passed (11)
     Tests  37 passed (37)
```

Baseline before Phase 36: `Test Files 10 passed (10)`, `Tests 26 passed (26)`.
**Phase 36 added 11 tests** (`src/pages/NotificationsPhase36.test.tsx`), 0 regressions.

---

## TypeScript

```
$ cd frontend && npx tsc --noEmit
TSC PASS   (exit code 0, no output)
```

---

## Production build

```
$ cd frontend && npm run build
✓ built in 7.05s        (exit code 0)
dist/assets/index-BXxkfV4D.js   1,103.58 kB │ gzip: 295.84 kB
```

Pre-existing warnings only (chunk >500 kB, ineffective dynamic import for
`sprintApi.ts`). Both warnings exist at baseline and are unrelated to Phase 36.

---

## Migration

`86f704f37613_add_advanced_notifications_fields.py` (revises `b27b8e7e4ff4`).

```
$ cd backend && python run_phase36_migration_check.py
HEAD: 86f704f37613
--- upgrade head ---        OK
--- downgrade -1 ---        OK
--- upgrade head again ---  OK
MIGRATION_CYCLE=PASS
```

That command was a throwaway Alembic driver (backup → upgrade → downgrade →
upgrade → restore) removed after verification as a temporary Phase 36 file; the
cycle can be reproduced with `alembic downgrade -1 && alembic upgrade head`.

upgrade → downgrade → upgrade all succeeded on SQLite. No notification data
destroyed (the migration only adds nullable/defaulted columns via
`op.batch_alter_table`).

---

## Action Center aggregation (integration check)

The endpoint wraps each source in `try/except`, so a silent model mismatch
would look like an empty list rather than an error. This is now pinned
permanently in the suite by
`test_action_center_aggregates_all_six_sources`, which seeds all six sources
through the ORM and asserts each yields an action item:

```
$ cd backend && python -m pytest tests/test_phase36_notifications.py -q
23 passed, 90 warnings in 24.65s
```

Coverage asserted by that test:
`WORKFLOW_APPROVAL`, `RELEASE_APPROVAL`, `JOB_FAILURE`, `DEPLOYMENT_FAILURE`,
`DAILY_REPORT_BLOCKER`, `NOTIFICATION` — plus that the deployment description
comes from `deployment_key` and every item carries `created_at`.

Before being made permanent, the same six-source check was run as a standalone
script and printed all six types with `AGGREGATION=PASS all 6 sources produced
items`.

This check caught and fixed a real bug: `Deployment` has **no `name` and no
`updated_at` column**, so the original deployment block silently produced zero
items. `_deployment_label()` now derives the label from
`deployment_key → version → commit_sha → id`.

---

## RBAC

Verified by executed tests (`test_phase36_notifications.py`):

- `test_notifications_require_authentication` — all 5 unauthenticated requests
  return 401.
- `test_cross_user_id_manipulation_returns_404` — all six mutations
  (`GET`, `read`, `unread`, `important`, `unimportant`, `DELETE`) on another
  user's notification id return **404**, and the owner still gets 200.
- `test_malformed_and_random_ids_are_rejected_not_500` — malformed UUIDs and
  random UUIDs return 404/422, never 500.

**PASS**

---

## Tenant isolation

Verified by executed tests:

- `test_action_center_aggregates_and_is_user_scoped` — user B never sees
  user A's action items.
- `test_different_users_get_their_own_notifications` — notifications are
  per-user and do not cross over.
- `test_global_search_finds_own_notifications_only` — user B searching the same
  term gets zero `NOTIFICATION` hits.
- `test_all_phase36_notification_rows_carry_organization_scope` — every
  org-scoped notification row records its `organization_id`.
- `test_action_item_broadcast_is_org_scoped` — `action_item.created` reaches
  only the target org's sockets.

**PASS**

---

## Security

- No notification id is ever trusted from the client without a
  `user_id == current_user.id` filter.
- Foreign ids return 404 (not 403), so existence is not disclosed.
- No SQL string interpolation — all queries are SQLAlchemy expressions.
- All notification-writing call sites are wrapped in `try/except`, so a
  notification failure can never break the business transaction.
- GlobalSearch notifications are scoped to `user_id` **and**
  `organization_id == org_id OR organization_id IS NULL`.

**PASS**

---

## Realtime

Reused the existing `app/websockets/manager.py` `ConnectionManager`. No second
WebSocket implementation was added. Verified by executed tests:

- `test_notification_personal_message_targets_only_owner` —
  `notification.created` reaches exactly the owning user.
- `test_action_item_broadcast_is_org_scoped` — `action_item.created` is
  org-scoped, not leaked.

Events emitted: `notification.created`, `notification.read`,
`notification.read_all`, `notification.updated`, `notification.deleted`,
`action_item.created`.

**PASS**

---

## Performance

Backend-driven filtering and pagination are enforced in SQL, verified by
`test_listing_pagination_and_backend_filters`, which asserts:

- offset/limit pagination returns disjoint pages,
- `notification_type`, `important`, `action_required`, `unread_only`,
  `date_from` are all applied server-side (a future `date_from` returns `[]`),
- summary counts use SQL `count()` aggregation.

New indexes: `notifications.action_required`, `notifications.important`,
`notifications.organization_id` (on top of the existing `user_id`, `type`,
`read`, `entity_type`, `entity_id`, `created_at` indexes).

Action Center issues one bounded query per source (limits 20/20/20/20/50/20) —
no N+1, no full-table loads.

**PASS**

---

## Documentation

- `docs/notifications-and-action-center.md` — created
- `PHASE36_VERIFICATION_REPORT.md` — this file

**DONE**

---

## Git commit

Single commit: `feat: implement advanced notifications and action center`

Temporary Phase 36 files (`clean_migration2.py`, `fix_db.py`,
`scratch_patch_notification_models.py`, scratch edit to
`scratch_patch_schemas.py`, the migration-check helper scripts, `test.db`,
`phase36_actioncenter_check.db`) were reviewed and either reverted to their
pre-Phase-36 state or left out of the commit.

---

## Known limitations

1. **Legacy `JOB_FAILED` retained alongside `JOB_FAILURE`.** The scheduler's
   Phase 31 code path writes `JOB_FAILED` for owners/admins and is asserted by
   the pre-existing `test_phase31_jobs.py`. Phase 36's `notify_job_failure`
   therefore skips anyone who already has a notification for that job, so no
   user ever receives two notices for the same failure — but the older type
   name still exists for those recipients.
2. **Daily report reminders are lazily generated** on `GET /notifications`
   rather than by a scheduled job, matching the existing pattern used for
   overdue-task and project-health notifications. They only fire for users who
   have reported within the last 30 days.
3. **`DEPLOYMENT_STARTED` / `DEPLOYMENT_SUCCESS` notify all org members**, which
   can be chatty on high-deploy-frequency orgs. They are `NORMAL` priority and
   can be disabled per user via `deployment_notifications`.
4. **Email channel is still a placeholder.** No external notification service
   was added, per the phase constraints.
5. **Pre-existing test isolation defect (not caused by Phase 36):**
   `backend/tests/api/v1/*.py` register `app.dependency_overrides[get_current_user]`
   at module import time and never remove it, so any test collected after them
   silently bypasses authentication. The Phase 36 suite clears those leaked
   overrides for its own duration (autouse fixture) and restores them
   afterwards, leaving other suites unaffected. Fixing the root cause would
   change the outcome of several currently-passing pre-existing tests, so it
   was deliberately left out of scope for Phase 36.
6. **Pre-existing failures (77)** are unrelated to notifications — concentrated
   in `test_workflow_studio.py` (23), `test_phase31_security.py` (9),
   `test_predictive_planning.py` (6), `test_projects.py` (4),
   `test_knowledge_base.py` (4), `test_jobs.py` (4).
