# Phase 42 — GitHub Analytics UI & Degraded State Experience — Verification Report

**Date:** 2026-10-06
**Scope:** Make the ProjectAnalytics GitHub section clearly distinguish loading /
not connected / no repository / success (incl. genuine zero activity) / degraded,
with a single explicit retry — without breaking the Phase 40 zero-count 200
degradation contract or the 5-minute success cache.

---

## 1. Existing GitHub behavior inspected

- `GET /api/v1/analytics/projects/{project_id}/github`
  (`backend/app/api/v1/analytics.py`) — Phase 40 reliability: any GitHub-side
  failure (revoked token, rate limit, 5xx, timeout, malformed payload)
  degrades to an all-zero 200; successful counts cached in-process
  (`GITHUB_COUNTS_TTL_SECONDS = 300`); failures never cached; no credentials
  in responses.
- Before Phase 42 the **identical** zero body was returned for three different
  situations: no repo configured, user not connected, and GitHub failure —
  indistinguishable from each other and from genuine zero activity.
- `frontend/src/components/ProjectAnalytics.tsx` — `gh === null` (request
  rejection) rendered "Connect GitHub to unlock repository analytics.", which
  was misleading in every failure scenario.
- Separate `ProjectGitHub.tsx` component (connection management UI) and
  `GitHubIntegrations.tsx` already handle connect/disconnect; untouched.
- `docs/analytics-route-inventory.md` and `PHASE40_VERIFICATION_REPORT.md`
  reviewed for the degradation/cache contract.

## 2. API contract change (smallest safe extension)

`GitHubAnalyticsResponse` gained one optional field:

```jsonc
"status": "ok" | "not_connected" | "no_repository" | "unavailable"
```

- Additive and defaulted (`"ok"`); existing consumers keep working — numeric
  fields, names, and types unchanged; no field removed or renamed.
- Old payloads without `status` are treated as `"ok"` by the frontend type
  (`status?: GitHubAnalyticsStatus`).
- No GitHub tokens, error details, or raw exceptions are ever exposed — the
  status is a coarse enum, not an error message.

Status semantics (backend):

| Situation | status | counts |
|---|---|---|
| Live/cached fetch succeeded (incl. empty repo) | `ok` | real counts (may be 0) |
| GitHub-side failure | `unavailable` | zeros |
| Project has no configured repository | `no_repository` | zeros |
| User has no GitHub integration | `not_connected` | zeros |

Failure responses remain HTTP 200 with zero counts (Phase 40 contract
preserved); failures are still never cached; the success cache and its TTL are
untouched.

## 3. UI states implemented (`ProjectAnalytics.tsx` GitHub card)

- **A. Loading** — existing full-panel loading pattern unchanged.
- **B. Not connected** — "GitHub is not connected. Connect GitHub in Settings…"
- **C. No repository** — "No GitHub repository is configured for this project."
- **D. Success** — existing metrics rows, unchanged layout.
- **E. Genuine zero activity** — with `status: "ok"`, zeros render as real
  metric rows (visually distinct from B/C/F).
- **F. Degraded** — non-blocking yellow warning banner: "GitHub data is
  temporarily unavailable…", a single **Retry** button, and no fake-looking
  zeros rendered as activity. Request rejection (network) shows a neutral
  "temporarily unavailable" status line. Rest of Project Analytics stays
  fully usable in every state.

UX: no page redesign; existing design-system classes; `role="status"` on
state messages for accessibility; disabled-state on the retry button while
in-flight; no animations; no new dependencies.

## 4. Retry behavior

- One explicit button click → one re-request through the existing
  `analyticsApi` client → backend cache respected (no cache bypass).
- Disabled while in-flight; no polling, no WebSockets, no auto-retry loop.
- Note: a degraded response is not cached, so a retry genuinely re-queries
  GitHub — matching the Phase 40 "failures are not cached" design.

## 5. Tests added

Backend — `backend/tests/test_phase42_github_states.py` (9 tests, GitHub fully
mocked, no network):
success `ok`; genuine zero activity is `ok` (not degraded); degraded
`unavailable` (no error-detail leakage); `no_repository`; `not_connected`;
exact response-shape compatibility; 401 unauthenticated; non-member 403/404;
no credentials (`ghs_testtoken`/`token`/`access_token`) in any response.

Frontend — `frontend/src/components/ProjectAnalytics.github.test.tsx`
(9 tests): loading; not connected; no repository; success metrics; zero
activity ≠ missing connection; degraded warning + no zeros rendered + retry
present; retry-once updates section (exactly 2 API calls); page remains usable
when degraded; rejected request doesn't crash the page.

Updated (contract pin, not weakening):
- `test_phase40_github_reliability.py` — `ZERO` now includes
  `status: "unavailable"`; success/retry-success fixtures include `ok`;
  repo-missing case now asserts `no_repository` + GitHub never called.
- `test_phase39_analytics_clients.py::test_project_github_no_repo_returns_zeros`
  — exact body now pins `status: "no_repository"`.

## 6. Security verification

- Authentication (401), org membership (403/404 for non-members), and
  `analytics.projects` permission checks unchanged and re-verified
  (Phase 38 matrix + Phase 40/42 endpoint tests).
- Project access check (project → its organization's membership) untouched.
- No credential/token/error-message leakage asserted explicitly in both
  Phase 40 (existing) and new Phase 42 tests.
- Cache still stores counts only, never credentials; failures never cached.

## 7. Results (actually run)

| Check | Command | Result |
|---|---|---|
| Focused backend | `pytest tests/test_phase42_github_states.py tests/test_phase40_github_reliability.py tests/test_phase38_analytics.py tests/test_phase41_workflow_analytics.py -q` | **71 passed** |
| Full backend | `python -m pytest tests -q` | **239 passed / 0 failed** (~4m36s) |
| Analytics contract validation | `pytest tests/test_phase40_github_reliability.py::test_frontend_analytics_time_urls_exist_in_backend tests/test_phase42_github_states.py tests/test_phase38_analytics.py -q` | **41 passed** |
| Frontend tests | `npx vitest run` | **46 passed (12 files)** |
| TypeScript | `npx tsc --noEmit` | **exit 0** |
| Production build | `npm run build` | **built successfully** |

(First full-suite run caught one stale Phase 39 contract pin; updated the pin
to the new explicit status and re-ran the full suite to green.)

## 8. Migration status

**No migration.** No schema changes; `alembic/versions` untouched. The status
field is a Pydantic-level contract extension only.

## 9. Remaining limitations

- `not_connected`/`no_repository`/`unavailable` are indistinguishable from each
  other in *old cached responses* only if a cache entry predates the deploy —
  in practice the in-process cache clears on restart, so this is a non-issue.
- The degraded banner offers no diagnostic reason by design (no GitHub error
  leakage); users wanting specifics must check server logs.
- Retry is manual-only per the spec; if GitHub stays down, the user sees the
  banner until they retry (deliberately no polling).
- Dashboard overview `open_github_prs/issues` (org-level) still uses the
  Phase 40 zero-degradation behavior without a status field — out of scope.
