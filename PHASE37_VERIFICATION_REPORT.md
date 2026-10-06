# PHASE 37 VERIFICATION REPORT

**Phase:** 37 — Regression & Technical Debt Elimination
**Date:** 2026-10-06
**Starting point:** `72f9a62` ("test: pin all six Action Center aggregation sources in the suite")

Every result below is an actually executed command. Nothing is asserted from code inspection alone.

---

## 1. Problems found

| # | Symptom | Count | Genuine bug? |
| --- | --- | --- | --- |
| 1 | `tests/test_workflow_studio.py` failures | 23 | No — order-dependent |
| 2 | `tests/test_phase31_security.py` failures | 9 | No — order-dependent |
| 3 | `tests/test_predictive_planning.py` failures | 6 | No — order-dependent |
| 4 | `tests/test_analytics.py::test_analytics_and_notifications` | 1 | **Yes — 2 real bugs** |
| 5 | `tests/test_delivery.py::test_delivery_flow` | 1 | **Yes — route shadowing** |
| 6 | `tests/api/api_v1/test_infrastructure.py` | 1 | Pre-existing, separate |
| 7 | Tracked DB artifacts (`devflow.db`, `test.db`, `perf_probe.db`) | — | Hygiene debt |

### Decisive isolation experiment

`test_workflow_studio.py` passed **25/25 in isolation**, which ruled out
implementation bugs and pointed at collection-order pollution:

```
$ python -m pytest tests/api tests/test_workflow_studio.py \
      tests/test_phase31_security.py tests/test_predictive_planning.py -q
24 failed, 16 passed

$ python -m pytest tests/test_workflow_studio.py \
      tests/test_phase31_security.py tests/test_predictive_planning.py -q
43 passed, 0 failed
```

So **all 38** "pre-existing" failures in the three priority areas had a single
root cause.

---

## 2. Root causes

### RC1 — Global `dependency_overrides` leak (caused all 38 failures)

`tests/api/v1/test_analytics_new.py`, `test_daily_reports.py` and
`test_daily_report_intelligence.py` each assigned

```python
app.dependency_overrides[deps.get_current_user] = override_get_current_user
app.dependency_overrides[deps.get_current_organization_id] = override_get_current_organization_id
```

at **module import time** — i.e. during *collection*, before any test ran — and
never removed them. Since `tests/api/…` is collected before `tests/test_…`,
every later test silently ran as a fake user: unauthenticated requests returned
200, and per-user queries returned the wrong (empty) results.

### RC2 — `UUID(UUID)` crash in project analytics

`app/api/v1/analytics.py:68` called
`UUID(project.organization_id)`, but `organization_id` is already a UUID
(`Uuid` column). `uuid.UUID(hex=...)` then raised
`AttributeError: 'UUID' object has no attribute 'replace'` → 500.

### RC3 — `status_distribution` shape mismatch

`ProjectAnalyticsResponse.status_distribution` is declared
`List[TaskStatusDistribution]` and the frontend does
`analytics.status_distribution.map(...)`, but
`analytics_service.get_project_analytics` returned a **dict**
(`{"TODO": 1, …}`) → `ResponseValidationError`.

### RC4 — `deadlines` buckets were hardcoded stubs

`get_project_analytics` returned
`{"overdue": overdue, "due_today": 0, "due_soon": 0, "future": 0, "no_deadline": 0}`.
Only `overdue` was ever computed, so `due_soon` was always 0.

### RC5 — `/analytics/delivery` route shadowing

Two routers were mounted on the **same path**:

- `analytics.router` → `GET /delivery` (registered `main.py:58`) returning a
  thin payload from `analytics_service.get_delivery_analytics`
- `delivery_metrics_router` → `GET /delivery` (registered `main.py:70`)
  returning the complete `DeliveryMetrics` shape including
  `pipeline_success_rate`

FastAPI resolves the first match, so the complete implementation was
**unreachable**. The frontend `DeliveryAnalytics` page reads
`metrics.pipeline_success_rate.toFixed(1)` from exactly this endpoint and
therefore crashed in production, not just in tests.

---

## 3. Fixes made

| Fix | File | Nature |
| --- | --- | --- |
| Moved auth overrides from import time into an autouse fixture with teardown | `tests/api/v1/test_analytics_new.py` | test infra |
| same | `tests/api/v1/test_daily_reports.py` | test infra |
| same | `tests/api/v1/test_daily_report_intelligence.py` | test infra |
| Removed the now-redundant defensive fixture from the Phase 36 suite | `tests/test_phase36_notifications.py` | test infra |
| `UUID(x)` → `x` (already a UUID) | `app/api/v1/analytics.py` | **real bug** |
| `status_distribution` dict → list of `{status, count}` | `app/services/analytics_service.py` | **real bug** |
| Implemented real deadline bucketing (`overdue`/`due_today`/`due_soon ≤7d`/`future`/`no_deadline`, DONE excluded) | `app/services/analytics_service.py` | **real bug** |
| `/analytics/delivery` now delegates to the complete `get_delivery_metrics` while **keeping** `require_organization_member` + `check_permission`; deleted the shadowing thin route and its now-unused service function/import | `app/api/v1/analytics.py`, `app/services/analytics_service.py` | **real bug** |
| Untracked generated SQLite DBs and gitignored them | `.gitignore`, 3 files | hygiene |

**Security preserved, not weakened.** The delivery route fix deliberately kept
the permission check that the shadowing route enforced:
`require_organization_member(...)` and `check_permission(db, member, "analytics.view")`.
No assertion was weakened and no test was skipped.

---

## 4. Tests actually executed

### Focused (affected files first)

```
$ python -m pytest tests/api tests/test_workflow_studio.py \
      tests/test_phase31_security.py tests/test_predictive_planning.py \
      tests/test_phase36_notifications.py -q
81 passed, 192 warnings in 75.83s

$ python -m pytest tests/test_delivery.py tests/test_analytics.py \
      tests/test_phase32_delivery.py -q
3 passed, 70 warnings in 12.26s

$ python -m pytest tests/test_phase31_security.py tests/test_phase31_realtime.py \
      tests/test_isolation_security.py tests/test_phase36_notifications.py \
      tests/test_workflow_security.py -q
49 passed, 151 warnings in 60.32s
```

### Complete backend suite (final)

```
$ python -m pytest tests -q --tb=line -p no:cacheprovider
158 passed, 296 warnings in 141.34s
```

**0 failures. 100% of the backend suite passes.**
(Phase 36 baseline: 77 failed, 81 passed → now 0 failed, 158 passed.)

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
✓ built in 7.05s        (exit code 0)
```

Pre-existing warnings only (chunk >500 kB, ineffective dynamic import for
`sprintApi.ts`) — both present at baseline, unrelated to this phase.

### Migration

```
HEAD: 86f704f37613
OK upgrade
OK downgrade
OK upgrade again
MIGRATION_CYCLE=PASS
```

The cycle was driven by a throwaway Alembic helper removed afterwards; it can be
reproduced with `alembic downgrade -1 && alembic upgrade head`.

### Security

Verified by executed tests in the security/isolation run above (49 passed):
- `test_notifications_require_authentication` — 401 for all unauthenticated requests
- `test_cross_user_id_manipulation_returns_404` — foreign ids 404 on all 6 mutations
- `test_action_center_aggregates_and_is_user_scoped` / `test_global_search_finds_own_notifications_only` — tenant isolation
- `test_isolation_security.py` — cross-tenant 403
- `test_workflow_security.py` — workflow RBAC

### Realtime

`tests/test_phase31_realtime.py` — passed in the security/realtime run
(49 passed total), covering org-scoped broadcast, personal-message targeting,
disconnect cleanup and the WebSocket handshake.

### Performance / DB integrity

```
$ python scripts/check_db_integrity.py sqlite:///./devflow.db
Result: ALL CHECKS PASSED — no integrity issues detected
INTEGRITY_EXIT=0

$ python scripts/perf_probe.py
13 endpoints measured, all ≤ 20 SELECTs (max 14)
No endpoint exceeded 20 SELECTs.
PERF_EXIT=0
```

No N+1 patterns introduced by the Phase 36 notification work.

---

## 5. Database artifacts

`backend/devflow.db`, `backend/test.db` and `backend/perf_probe.db` were all
**tracked** and perpetually showed as modified.

- `test.db` — generated by `tests/conftest.py` (`sqlite:///./test.db`), pure test data.
- `perf_probe.db` — explicitly "a throwaway SQLite database" per its own docstring.
- `devflow.db` — generated local dev database, reprovisionable via
  `alembic upgrade head` (documented in `docs/local-development.md:39`).

All three were untracked with `git rm --cached` — **files left intact on disk,
no data deleted** — and `backend/*.db` / `*.sqlite3` added to `.gitignore`.

---

## 6. Final git status

```
On branch master, clean.
 nothing to commit (after the Phase 37 commit)
```

Commit: `chore: eliminate regression and harden test isolation`

---

## 7. Remaining known limitations

1. **`backend/perf_probe.py` will recreate its DB** on next run; it is now
   untracked, which is the intended behaviour for a throwaway probe.
2. **Deprecation warnings remain** (Pydantic `class Config`, SQLAlchemy
   `declarative_base()`, FastAPI `on_event`). They are cosmetic, appear at
   baseline, and were deliberately not touched to avoid churn in a cleanup phase.
3. **`tests/api/v1/test_infrastructure.py`** — passed in the final full run;
   its earlier `KeyError` was an artefact of the same override leak.
4. **Two analytics routers still share the `/analytics` prefix.** The duplicate
   `/delivery` route was removed, but `/dora` is only defined by
   `delivery_metrics_router`. Consolidating the two routers into one would be a
   worthwhile follow-up but is a structural change outside this phase's scope.
5. **Deadline buckets use a 7-day `due_soon` window** — chosen to match the
   existing task-due-soon notification behaviour. If product wants a different
   horizon it is a one-line change in `_deadline_analysis`.
