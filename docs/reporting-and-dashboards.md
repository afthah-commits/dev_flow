# Phase 18: Advanced Reporting + Custom Dashboards

## Overview
Phase 18 introduces powerful enterprise reporting capabilities to DevFlow. By leveraging data collected from Phase 1 through Phase 17, DevFlow now offers a customizable dashboard and reporting engine to visualize project health, team workloads, delivery metrics, and security audits.

## Key Features
1. **Reporting Engine:** High-level metrics aggregated natively via SQLAlchemy without N+1 queries.
2. **Dashboards:** Users can configure multiple organization-scoped dashboards and populate them with custom widgets.
3. **Data Export:** Reports can be exported as raw JSON/CSV, respecting all filters applied.
4. **Data Isolation:** Enforced via X-Organization-Id across all endpoints to maintain strict multi-tenant boundary segregation.

## Architecture
- Backend routes are implemented in pp.api.v1.reports and pp.api.v1.dashboards.
- Core aggregation is in pp.core.reports.
- Frontend interfaces are rendered through Dashboards.tsx and Reports.tsx powered by eportApi.ts.
- The engine uses native Recharts for dynamic visual rendering.

## Security 
All routes utilize Phase 17's Custom Roles System by enforcing eports.view, dashboards.manage, and eports.export permissions via the check_permission interceptor.

