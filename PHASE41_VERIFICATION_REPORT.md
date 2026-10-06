# Phase 41 — Workflow Analytics Completion — Verification Report

**Date:** 2026-10-06
**Scope:** Replace the two remaining placeholders in org-level workflow analytics
(`average_execution_time`, `blocked_executions`) with real, deterministic
calculations based on existing execution data. No schema changes. No new statuses.
No frontend redesign.

---

## 1. What was inspected

- Phase 40 commits (`9e0f8e4 feat: harden analytics reliability and contracts`,
  `1cce2cf fix: align analytics clients with backend contracts`).
- `get_workflow_analytics` in `backend/app/services/analytics_service.py` — both
  fields were hard-coded placeholders (`0.0` / `0`).
- `Workflow`, `WorkflowExecution`, `WorkflowApproval`, `WorkflowExecutionEvent`
  models in `backend/app/models/workflow.py`.
- Execution status values: `ACTIVE`, `COMPLETED`, `FAILED` (string column;
  comment + usage in `workflow_studio.py` confirm exactly these three).
- `started_at` (nullable=False, default now) and `completed_at` (nullable=True)
  timestamps on `WorkflowExecution`.
- `WorkflowAnalyticsResponse` schema in `backend/app/schemas/analytics.py`
  (contract unchanged).
- Per-workflow analytics endpoint (`GET /workflows/{id}/analytics`) and the
  frontend page `frontend/src/pages/WorkflowAnalytics.tsx`, which consumes that
  endpoint — not the org-level one.
- Route/auth layer: `GET /api/v1/analytics/workflow` enforces
  `require_organization_member` + `analytics.view` permission (unchanged).
- Existing tests: `test_workflow_studio.py::test_workflow_analytics_endpoint`,
  `test_phase38_analytics.py` (auth/RBAC/isolation matrix incl. `/workflow`).

## 2. Previous placeholders

```python
"average_execution_time": 0.0,
"blocked_executions": 0
```

## 3. Actual implementation

Single file changed: `backend/app/services/analytics_service.py`
(`get_workflow_analytics`). Both new calculations reuse the existing
org-scoped execution query (join `WorkflowExecution → Workflow.organization_id`),
preserving tenant isolation exactly as before.

### average_execution_time — calculation rules

- Unit: **seconds** (float), preserving the existing response field/type.
- Included: executions where **both** `started_at` and `completed_at` are
  present (i.e. only finished executions contribute).
- Excluded: incomplete executions (`completed_at IS NULL`) and any row with a
  missing timestamp — excluded, not treated as zero.
- Zero executions / zero valid durations → `0.0`.
- Deterministic: pure mean of `(completed_at - started_at).total_seconds()`.
- Computed from the already-loaded execution rows (the endpoint previously
  loaded them all for counts), so no extra query and no DB-specific SQL.

Note: the schema declares `started_at` as `nullable=False`, so a missing start
timestamp cannot occur in production; the Python guard (`e.started_at and
e.completed_at`) is defense in depth. `completed_at IS NULL` is the real
missing-timestamp case and is covered by tests.

### blocked_executions — definition

The existing domain model **does** encode blocked state, without inventing
anything new:

- `workflow_studio.apply_transition` returns `PENDING_APPROVAL` when an
  approval gate fires and records an `APPROVAL_REQUESTED` execution event;
  the execution itself stays `status="ACTIVE"` until the gate resolves.
- Therefore: **blocked = ACTIVE execution whose (entity_type, entity_id) has a
  PENDING `WorkflowApproval` row.**

Implementation: a single correlated `EXISTS` subquery (`COUNT`) on
`workflow_approvals` joined on entity type/id with `status == "PENDING"`,
ANDed with `WorkflowExecution.status == "ACTIVE"` and the same org scoping.

- FAILED executions are **not** counted as blocked (explicitly tested).
- APPROVED/REJECTED/CANCELLED approvals do not block (explicitly tested).
- Plainly ACTIVE executions without a pending gate are not blocked.
- Zero results → `0`.
- Tenant isolation and org scoping inherited from the base query.

## 4. Frontend

`frontend/src/pages/WorkflowAnalytics.tsx` consumes the **per-workflow**
endpoint (`workflowApi.getAnalytics`), which already computed real values
(`avg_execution_seconds`, etc.) since Phase 30/31 — no placeholders, no changes
required or made. Zero values, `null → "—"`, loading, empty, and error states
were reviewed and remain correct. Contract unchanged
(`test_phase40_github_reliability.py::test_frontend_analytics_time_urls_exist_in_backend`
passes).

## 5. Tests added

`backend/tests/test_phase41_workflow_analytics.py` — 12 focused tests,
deterministic fixed timestamps, no network:

1. zero executions → avg 0.0
2. single completed execution → exact avg
3. multiple completed executions → mean avg
4. missing end timestamp excluded from avg (incl. COMPLETED without end)
5. missing start timestamp: pinned as schema-forbidden (`nullable=False`)
6. correct average (covered by 2/3)
7. zero average when no valid durations
8. blocked count = 1 for ACTIVE + PENDING approval
9. FAILED execution with pending approval → not blocked (`failed_executions == 1`)
10. APPROVED approval → not blocked; ACTIVE without approval → not blocked
11. organization isolation (second org sees zeros)
12. response contract shape validated against `WorkflowAnalyticsResponse`

RBAC/auth/permission checks for `/api/v1/analytics/workflow` were already
parametrized across the whole analytics surface in `test_phase38_analytics.py`
(401 unauthenticated, org-header rejection, 403 non-member) and remain green —
not duplicated here.

## 6. Security verification

- Unauthenticated → 401: `test_phase38_analytics.py::test_analytics_endpoints_require_authentication[/api/v1/analytics/workflow]` ✅
- Missing org context → rejected (400/403): `test_analytics_endpoints_require_org_header` ✅
- Non-member / foreign org → 403, no leakage ✅
- Service queries scoped via `Workflow.organization_id == org_id` (unchanged) ✅
- Isolation of new metrics: `test_workflow_analytics_isolated_by_organization` ✅
- No security check weakened; no new endpoint; no new permission.

## 7. Results (actually run)

| Check | Command | Result |
|---|---|---|
| Focused tests | `python -m pytest tests/test_phase41_workflow_analytics.py -q` | **12 passed** |
| Full backend | `python -m pytest tests -q` | **230 passed / 0 failed** (~4m26s) |
| Analytics contract scan | `pytest tests/test_phase40_github_reliability.py::test_frontend_analytics_time_urls_exist_in_backend tests/test_phase38_analytics.py -q` | **32 passed** |
| Frontend tests | `npx vitest run` | **37 passed (11 files)** |
| TypeScript | `npx tsc --noEmit` | **exit 0** |
| Production build | `npm run build` | **built in 8.37s** |

## 8. Performance

- No N+1: the average is computed from the already-loaded rows; blocked count
  is one additional aggregate `COUNT ... EXISTS` query per request (same
  org-scoped join). Net: +1 SQL statement vs Phase 40, no per-row queries.
- No large refactor performed.

## 9. Migration status

**No migration created.** The existing schema already contains everything
required (`workflow_executions.started_at/completed_at/status`,
`workflow_approvals.entity_type/entity_id/status`). `alembic/versions`
untouched (34 files, unchanged).

## 10. Remaining limitations

- **Blocked definition granularity:** approvals are matched on
  `(entity_type, entity_id)`, not by `execution_id` — `WorkflowApproval` has no
  execution FK. If two executions run concurrently for the same entity, a
  pending approval blocks both. This matches how `apply_transition` itself
  looks up pending approvals (`WorkflowApproval.entity_id == execution.entity_id`),
  so it is consistent with the engine, but it is entity-level, not
  execution-level, precision.
- Condition-failed stops (`CONDITION_FAILED` events, `BLOCKED` simulation
  result) leave the execution ACTIVE without an approval row; they are **not**
  counted as blocked, because the persisted model has no durable
  "condition-blocked" state and inventing one was out of scope.
- `average_execution_time` is a simple mean over completed executions; no
  time-window filtering exists on this endpoint (pre-existing).
- Org-level analytics response shape is unchanged; the frontend continues to
  use the richer per-workflow endpoint.
