# Analytics Route Inventory

> Phase 38. Every `/api/v1/analytics/*` endpoint now has exactly one
> authoritative route, all served by `app/api/v1/analytics.py` (`router`),
> registered once in `app/main.py` under `{API_V1_STR}/analytics`.
> The separate `delivery_metrics_router` (previously also mounted on
> `/analytics` in `app/api/v1/delivery.py`) was removed.

Auth = `deps.get_current_user` (401 without a token) on every endpoint below.
Org = `deps.get_current_organization_id` (`X-Organization-Id` header) +
`deps.require_organization_member` (403 for non-members).
Perm = `check_permission(db, member, …)` from `app/api/v1/reports.py`.

| Endpoint | Method | Service (`app/services/analytics_service.py`) | Permission | Frontend consumer | Tests |
| --- | --- | --- | --- | --- | --- |
| `/dashboard` | GET | `get_dashboard_overview` | `analytics.view` | `lib/analyticsApi.ts` → Dashboard | `test_phase38_analytics.py::test_executive_and_dashboard_scoping` |
| `/executive` | GET | `get_executive_analytics` | `analytics.view` | `pages/analytics/ExecutiveDashboard.tsx` | same |
| `/projects/{project_id}` | GET | `get_project_analytics` | `analytics.projects` | `pages/analytics/ProjectAnalytics.tsx`, `lib/analyticsApi.ts` | `test_phase38_analytics.py::test_project_analytics_scoped_and_typed`, `test_analytics.py` |
| `/teams/{team_id}` | GET | `get_team_analytics` | `analytics.view` | `pages/analytics/TeamAnalytics.tsx` | — |
| `/sprints/{sprint_id}` | GET | `get_sprint_analytics` | `analytics.view` | `pages/analytics/SprintAnalytics.tsx` | — |
| `/delivery` | GET | `get_delivery_metrics` | `analytics.view` | `lib/deliveryAnalyticsApi.ts` → `pages/DeliveryAnalytics.tsx` | `test_phase38_analytics.py` (shape + isolation), `test_delivery.py` |
| `/dora` | GET | `get_dora_metrics` | `analytics.view` | `lib/deliveryAnalyticsApi.ts` → `pages/DeliveryAnalytics.tsx` | `test_phase38_analytics.py::test_dora_contract`, `test_delivery.py` |
| `/productivity` | GET | `get_time_analytics` | `analytics.view` | `lib/timeApi.ts` → `pages/ProductivityAnalytics.tsx` | — |
| `/workflow` | GET | `get_workflow_analytics` | `analytics.view` | — | `test_phase38_analytics.py::test_analytics_member_can_read_own_org` |
| `/automation` | GET | `get_automation_analytics` | `analytics.view` | — | `test_analytics_endpoints_require_authentication` etc. |
| `/clients` | GET | `get_client_analytics` | `analytics.view` | — | same |
| `/knowledge` | GET | `get_knowledge_analytics` | `analytics.view` | — | same |
| `/collaboration` | GET | `get_collaboration_analytics` | `analytics.view` | — | same |
| `/usage` | GET | `get_usage_analytics` | `analytics.view` | — | `test_analytics_member_can_read_own_org` |
| `/team-workload` | GET | `get_team_workload` | `analytics.view` | `ProductivityAnalytics.tsx` (`timeApi.getTeamWorkload`) | `test_phase39_analytics_clients.py` |
| `/projects/{id}/github` | GET | `get_project_github_analytics_api` (GitHubService) | `analytics.projects` | `ProjectAnalytics.tsx` (`analyticsApi.getGitHubAnalytics`) | `test_phase39_analytics_clients.py` |
| `/query` | POST | `execute_analytics_query` | `analytics.view` | — | — |
| `/export` | POST | — | `analytics.view` | — | — |

Out-of-prefix routes called by the frontend but served elsewhere (unchanged):
`/api/v1/projects/{id}/infrastructure/analytics` (infrastructure.py),
`/api/v1/integrations/usage/analytics` (integrations.py),
`/api/v1/workflows/{id}/analytics` (workflows.py).

## Notes

- `/delivery` and `/dora` moved into `analytics.py` in Phase 38. The
  implementation lives in the service layer (`analytics_service.py`), moved
  verbatim from `delivery.py`; URLs, query params (`project_id`) and response
  payloads are unchanged.
- `get_workflow_analytics` previously queried a non-existent
  `WorkflowExecution.organization_id` column (500 on every call). It now joins
  through `Workflow.organization_id`.
- Phase 38 left two client/route mismatches (documented above). **Phase 39
  resolved both** by adding the missing routes rather than deleting live
  consumers: `/team-workload` (per-member workload for the org's teams, reusing
  the previously orphaned `TeamWorkloadItem` schema) and
  `/projects/{id}/github` (commit/PR/issue counts via the existing
  `GitHubService`; a project with no connected repo returns zeros so the panel
  renders its "connect GitHub" fallback instead of erroring). Both enforce
  `require_organization_member` + `check_permission`. `ProductivityAnalytics.tsx`
  also loads stats and workload independently so a workload failure can no longer
  blank the page. See PHASE39_VERIFICATION_REPORT.md.
- **Phase 40 hardening:** `/projects/{id}/github` now (a) degrades any GitHub-side
  failure (revoked token, rate limit, 5xx, timeout, malformed payload) to a
  zero-count 200 instead of surfacing GitHub errors, and (b) caches successful
  aggregate counts in-process for 5 min (`GITHUB_COUNTS_TTL_SECONDS` in
  `analytics.py`; counts only — never credentials; failures are not cached so
  the next request retries). Connected-path behavior is pinned by mocked tests in
  `backend/tests/test_phase40_github_reliability.py`.
- **`workload_percentage` semantics:** tracked hours ÷ estimated hours × 100;
  100% == estimates fully consumed; >100% over capacity (frontend renders red);
  zero estimates → 0 (no division blowup).
- **Contract protection:** the static contract scan in
  `test_phase40_github_reliability.py::test_frontend_analytics_time_urls_exist_in_backend`
  cross-checks every `api.*(...)` URL in `frontend/src` against the registered
  FastAPI routes and fails on any nonexistent endpoint or duplicate backend
  route. Run with: `cd backend && python -m pytest
  tests/test_phase40_github_reliability.py::test_frontend_analytics_time_urls_exist_in_backend`
