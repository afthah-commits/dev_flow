# PHASE 38 VERIFICATION REPORT

**Phase:** 38 — Analytics Platform Consolidation & Reliability
**Date:** 2026-10-06
**Starting point:** `23d49f5` ("chore: drop unused pytest import from phase 36 notification tests")

Every result below is an actually executed command. Nothing is asserted from code inspection alone.

---

## Scope

Consolidate analytics routing so every `/api/v1/analytics/*` endpoint has
exactly one authoritative route, without breaking API contracts. Deprecation
warnings and the `due_soon` 7-day horizon were explicitly out of scope and
were not touched. No database changes were required, so no migration was created.

---

## Router changes

**Before (Phase 37 end-state):** two routers mounted on the same
`{API_V1_STR}/analytics` prefix:

- `analytics.router` (main.py:58) — 15 endpoints, including a `/delivery`
  wrapper that delegated to `delivery.py`
- `delivery_metrics_router` (main.py:70, defined in `app/api/v1/delivery.py`) —
  the complete `/delivery` + `/dora` implementations

**After:** one router. `analytics.router` serves all 16 endpoints.

1. Moved `get_delivery_metrics` and `get_dora_metrics` **verbatim** from
   `app/api/v1/delivery.py` into the service layer
   (`app/services/analytics_service.py`) — logic stays out of routers.
2. `analytics.py` now defines `/delivery` and `/dora` directly, each keeping
   `require_organization_member` + `check_permission(db, member, "analytics.view")`.
   `/delivery` gained the `project_id` query param that the frontend already
   sends (`deliveryAnalyticsApi.getDeliveryMetrics(projectId?)`).
3. Deleted `delivery_metrics_router` and its registration in `main.py`.
4. Removed dead imports (`TaskStatus` from delivery.py,
   `GitHubAnalyticsResponse` from analytics.py).

**URLs, methods, query params, response payloads, auth and permissions are
unchanged.** No frontend files were modified.

### Bonus fix (real bug found during contract check)

`get_workflow_analytics` queried `WorkflowExecution.organization_id`, a column
that does not exist on that model — every `GET /analytics/workflow` returned a
500 (`AttributeError: type object 'WorkflowExecution' has no attribute
'organization_id'`). It now joins through `Workflow.organization_id`.

---

## Endpoint inventory

See [docs/analytics-route-inventory.md](docs/analytics-route-inventory.md) for
the full table (endpoint / method / service / permission / frontend consumer /
test coverage).

Uniqueness verified programmatically:

```
$ python - <<'EOF'  (against app.main.app)
DUPLICATE (path,methods): none
EOF
```

`/api/v1/analytics/delivery` and `/api/v1/analytics/dora` are both present and
served by `analytics.router`.

---

## Contract check highlights

- **Delivery** returns the complete `DeliveryMetrics` shape the frontend reads
  (`pipeline_success_rate`, `successful_deployment_rate`, …) — asserted field
  by field, all numeric — and honours `project_id` filtering.
- **Project analytics** returns `status_distribution` as a list of
  `{status, count}` and correct deadline buckets (`due_soon=1`, `future=1`).
- **DORA** returns `insufficient_data` with <2 deployments and computes
  `change_failure_rate` (`"50.0%"`) with data.
- **Dashboard/Executive** scoped to the caller's org (`total_projects` 0 → 1
  after seeding).

---

## Security & tenant isolation (all executed)

`tests/test_phase38_analytics.py` (31 tests):

- `test_analytics_endpoints_require_authentication` — all 11 org-scoped
  analytics GETs return **401** unauthenticated.
- `test_analytics_endpoints_require_org_header` — no org context → 400/403.
- `test_analytics_rejects_non_member_with_foreign_org_header` — non-member with
  a foreign `X-Organization-Id` → **403** on dashboard/executive/delivery/dora.
- `test_delivery_metrics_never_leaks_other_orgs_deployments` — org A's failed
  deployment count is 1; org B, in its own deployment-free org, sees 0.
- `test_analytics_member_can_read_own_org` — valid member gets 200.
- Project-level endpoint rejects a foreign user (`test_analytics.py`, 403/404).

No security check was removed or weakened during consolidation; `/delivery`
and `/dora` actually **gained** the `analytics.view` permission check that
`delivery_metrics_router` never had (it only did org-membership).

---

## Tests actually executed

### Focused

```
$ python -m pytest tests/test_phase38_analytics.py tests/test_analytics.py \
      tests/test_delivery.py tests/test_phase32_delivery.py -q
34 passed, 108 warnings in 33.52s
```

### Full backend

```
$ python -m pytest tests -q --tb=line -p no:cacheprovider
189 passed, 334 warnings in 160.84s
```

Target was 158+ passed / 0 failed → **189 passed / 0 failed** (31 new Phase 38
tests, 158 pre-existing still passing).

### Frontend

```
$ npx vitest run
Test Files  11 passed (11)
     Tests  37 passed (37)
```

### TypeScript

```
$ npx tsc --noEmit
TSC PASS (exit 0)
```

### Production build

```
$ npm run build
✓ built in 6.62s        (exit code 0)
```

### Migration

No database changes were made → **no migration created** (per phase rules).

---

## Known limitations

1. **`due_soon` horizon unchanged** at 7 days, as instructed.
2. **Deprecation warnings untouched**, as instructed (out of scope).
3. **Two frontend API calls target non-existent backend routes** (pre-existing,
   documented in the inventory): `analyticsApi.getProjectGitHubAnalytics` →
   `/analytics/projects/{id}/github` (no callers — dead client code) and
   `timeApi.getTeamWorkload` → `/analytics/team-workload` (called by
   `ProductivityAnalytics.tsx`, which already renders its main metrics from the
   working `/analytics/productivity` call, so the page functions; the workload
   card silently fails). Creating these endpoints would be new feature work —
   out of scope for Phase 38 — and deleting the client functions risks touching
   UI behaviour beyond this phase's mandate.
4. `/teams/{team_id}`, `/sprints/{sprint_id}` and several org-level endpoints
   have no dedicated pytest coverage yet (they are exercised by the parametrized
   auth/org tests); their service logic is unchanged from earlier phases.

---

## Git

Commit: `refactor: consolidate analytics routing`

Changed files (reviewed, focused diff):

- `backend/app/api/v1/analytics.py` — owns `/delivery` + `/dora`; dead import removed
- `backend/app/api/v1/delivery.py` — `delivery_metrics_router` block removed; dead import removed
- `backend/app/main.py` — second `/analytics` router registration removed
- `backend/app/services/analytics_service.py` — delivery/dora service functions + workflow join fix
- `backend/tests/test_phase38_analytics.py` — new (31 tests)
- `docs/analytics-route-inventory.md` — new
- `PHASE38_VERIFICATION_REPORT.md` — new

No generated/local DB files were committed; `backend/*.db` is gitignored since
Phase 37.
