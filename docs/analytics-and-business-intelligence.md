# Analytics and Business Intelligence Platform

DevFlow Phase 33 introduces a robust, cross-tenant analytical overlay intended for executive and programmatic data extraction. 

## Architecture

The Analytics system is built directly atop existing DevFlow operational data stores to avoid synchronization lag and to provide deterministic results. Aggregations use native database features like `COUNT()`, `SUM()`, and `GROUP BY` via SQLAlchemy instead of fetching large datasets into the Python layer or React frontend. 

The core metrics are structured into various thematic areas:
1. Executive Dashboards
2. Project and Sprint Analytics
3. Delivery Intelligence
4. Time & Productivity
5. Workflow & Automation Health
6. Knowledge Base Utilization
7. Collaboration Engagement
8. Client Request Overview
9. Global Usage Constraints

## API Endpoints

- `GET /api/v1/analytics/executive`: Returns an overview across projects, delivery, sprints, and workflow statuses.
- `GET /api/v1/analytics/projects/{id}`: Deep dive into project completion, blockers, velocity, and health scores.
- `GET /api/v1/analytics/teams/{id}`: Overview of team workloads, completion rates, and average cycle times.
- `GET /api/v1/analytics/sprints/{id}`: Detailed sprint velocity, burndown points, and scope variations.
- `GET /api/v1/analytics/delivery`: Evaluates deployment metrics (lead time, failure rate, frequency).
- `GET /api/v1/analytics/productivity`: Tracks organization-wide time entry variance and compliance.
- `GET /api/v1/analytics/automation`: Outlines automation triggers and error ratios.
- `GET /api/v1/analytics/knowledge`: Summarizes spaces, active authors, and document views.
- `POST /api/v1/analytics/query`: A flexible Generic query API that allows dashboard widgets to pull specifically requested metrics (must be explicitly mapped in the whitelist).

## RBAC & Tenant Isolation

Tenant isolation is strictly verified on every analytics endpoint. 

The API uses `deps.require_organization_member(db, user_id, org_id)` combined with `X-Organization-Id` checks. Even generic queries via `POST /api/v1/analytics/query` perform database filtering appending `.filter(Entity.organization_id == org_id)`.

Access control uses the `check_permission` function:
- `analytics.executive`
- `analytics.projects`
- `analytics.teams`
- `analytics.view` (general queries)

## Realtime Invalidations

Dashboards trigger real-time updates through DevFlow's Phase 15 WebSockets (using generic `dashboard.updated` or `analytics.updated` events). The frontend throttles refreshes to ensure the database is not hammered.

## Export & Dashboards

Dashboards can be customized using the Phase 18 layout engine. Exports use standard DevFlow strategies (CSV format available via generic API or frontend JSON mapping).
