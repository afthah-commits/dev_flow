# PHASE 40 VERIFICATION REPORT

**Phase:** 40 — GitHub Analytics Reliability & Analytics Client Contract Hardening
**Date:** 2026-10-06
**Starting point:** `1cce2cf` (Phase 39; backend 199 passed / 0 failed)

Every result below is from an actually executed command.

---

## What was inspected

- `PHASE39_VERIFICATION_REPORT.md`, `docs/analytics-route-inventory.md`
- `backend/app/api/v1/analytics.py` (`get_project_github_analytics_api`)
- `backend/app/services/github_service.py` (`GitHubService`, `decrypt_token`, `_handle_response`)
- `backend/app/services/analytics_service.py::get_team_workload` + `TeamWorkloadItem` schema
- `frontend/src/pages/ProductivityAnalytics.tsx` workload rendering, `frontend/src/types/time.ts`
- All frontend API clients (`src/lib/*.ts`) and the Phase 39/40 test suites
- Repo-wide search for GitHub analytics references

## 1. GitHub analytics reliability

`GET /analytics/projects/{id}/github` in `analytics.py`:

- **Failure degradation.** Any GitHub-side failure now degrades to a zero-count
  `200` so the ProjectAnalytics panel renders its fallback instead of surfacing
  a GitHub error. Previously a GitHub rate-limit (`403`) or revoked token
  (`401`) propagated to the caller, indistinguishable from a DevFlow permission
  error. Covered: revoked token (401), rate limit (403), upstream 5xx, network
  timeout (`httpx.TimeoutException`), malformed/unexpected payload.
- **Lightweight in-process TTL cache** (`GITHUB_COUNTS_TTL_SECONDS = 300`):
  aggregate counts only, keyed by project + repo, capped at 256 entries with
  stale-entry eviction. No Redis/Celery; nothing sensitive cached — only the
  five count integers, never tokens. **Failures are deliberately not cached**,
  so a transient GitHub outage is retried on the next request rather than
  pinning zeros for 5 minutes (a bug the tests caught in my first draft).
- **No architecture change:** reuses `GitHubService` and the existing models;
  the three upstream calls target distinct endpoints (no repeated identical
  requests within a call).

## 2. GitHub connected-path test coverage

`backend/tests/test_phase40_github_reliability.py` — 19 tests, external GitHub
API fully mocked (`AsyncMock` on `GitHubService`); **zero real network requests**:

| # | Scenario | Assertion |
|---|---|---|
| 1 | Connected success path | correct counts (3 commits, 2/1 PRs, 1/1 issues) |
| 2 | Cached within TTL | service awaited exactly once across 2 calls |
| 3 | TTL expiry | re-fetched after expiry |
| 4 | Revoked token (401) | 200 + zeros |
| 5 | Rate limit (403) | 200 + zeros |
| 6 | Upstream 5xx | 200 + zeros |
| 7 | Timeout | 200 + zeros |
| 8 | Malformed response | 200 + zeros |
| 9 | Failure not cached | 2nd call retries and succeeds |
| 10 | Repo missing | 200 + zeros, GitHub service untouched |
| 11 | Unauthenticated | 401 |
| 12 | Foreign-org member | 403/404 |
| 13 | No credentials exposed | `ghs_testtoken` absent from response body; no `access_token` field |

Plus 6 workload-semantics edge cases (below) — no external calls anywhere.

## 3. Workload semantics decision

Inspected schema (`TeamWorkloadItem`), service, frontend, tests, and docs.
**The existing formula is correct and consistent** — frontend renders
`> 100%` red (over-capacity) and `< 100%` blue, matching
`workload_percentage = tracked_hours / estimated_hours × 100`. No formula
change. Instead, semantics are now documented (route inventory) and the edge
cases are pinned by tests:

- zero estimates + zero tracking → `0%` (no division blowup)
- exact capacity (4h est / 4h tracked) → `100%`
- over capacity (2h est / 8h tracked) → `400%`
- tracked hours but no estimates → `0%`, tracked hours still reported
- no team membership → empty list

## 4. Analytics contract validation

Static, deterministic, no network: `test_frontend_analytics_time_urls_exist_in_backend`

- Extracts every `api.get/post/patch/delete(...)` URL from `frontend/src/**/*.{ts,tsx}`
- Normalizes template-literal interpolations to single-segment placeholders
- Matches each against registered FastAPI routes (param segments as `[^/]+`)
- Fails on any nonexistent endpoint reference **and** on any duplicate backend
  route (globally, not just analytics)
- Sanity-asserts the scan actually found the analytics clients (≥10 URLs)

Run: `cd backend && python -m pytest tests/test_phase40_github_reliability.py::test_frontend_analytics_time_urls_exist_in_backend` → passes (part of the normal suite, so drift cannot return silently).

## 5. Security verification (executed)

- Unauthenticated `/analytics/projects/{id}/github` → **401** (test)
- Foreign-org member → **403/404** (test)
- Org membership + `check_permission(..., "analytics.projects")` unchanged from Phase 39 (route diff preserves both)
- No credentials in any response (asserted); cache stores counts only
- GitHub-side errors no longer leak status codes/details to analytics callers

## 6. Backend test result

```
$ python -m pytest tests/test_phase40_github_reliability.py tests/test_phase39_analytics_clients.py -q
29 passed

$ python -m pytest tests -q --tb=line -p no:cacheprovider
218 passed, 376 warnings in 190.35s (0:03:10)   # target 199+ ✓
```

## 7. Frontend test result

```
$ npx vitest run
Test Files  11 passed (11)
     Tests  37 passed (37)
```

## 8. TypeScript / build

```
$ npx tsc --noEmit   → exit 0 (TSC PASS)
$ npm run build      → ✓ built in 7.40s, exit 0
```

## 9. Migration status

No database schema changes → **no migration created** (per phase rules).

## 10. Files changed

- `backend/app/api/v1/analytics.py` — failure degradation + TTL cache on the GitHub counts route
- `backend/tests/test_phase40_github_reliability.py` — new (19 reliability/semantics/contract tests)
- `docs/analytics-route-inventory.md` — Phase 40 hardening notes, workload semantics, contract-check instructions
- `PHASE40_VERIFICATION_REPORT.md` — this file

## Remaining limitations

- The TTL cache is per-process: multi-worker deployments get one cache per worker (acceptable — worst case is one extra GitHub call per worker per 5 min).
- Degraded (zero-count) responses are indistinguishable from a genuinely empty repo at the API level; the panel treats both as "show fallback", which matches existing UX.
- `average_execution_time`/`blocked_executions` in workflow analytics remain placeholders (pre-existing, out of scope).
- Deprecation warnings (Pydantic/FastAPI) remain, out of scope per instructions.
