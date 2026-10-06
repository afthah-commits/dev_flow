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
- Known pre-existing gaps, deliberately not "fixed" here (they would create
  endpoints nobody calls): the frontend's `analyticsApi.getProjectGitHubAnalytics`
  targets `/analytics/projects/{id}/github`, which no backend route serves, and
  `timeApi.getTeamWorkload` targets `/analytics/team-workload`, which also does
  not exist. `getProjectGitHubAnalytics` has no callers; `getTeamWorkload` is
  called by `ProductivityAnalytics.tsx`, which already renders from the working
  `/analytics/productivity` call. See PHASE38_VERIFICATION_REPORT.md.
