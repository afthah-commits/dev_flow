# Daily Report Intelligence

The Daily Report Intelligence and Team Reporting module introduces aggregate capabilities for Phase 34's base implementation, surfacing organization-level progress.

## Overview
It implements specific aggregation points covering:
1. **Daily Summaries:** Aggregated cross-team performance metrics highlighting active progress against specific dates.
2. **Weekly Trend Rollups:** A chronological view plotting 7-day activity metrics (Task completion rate, reports submitted, blockers).
3. **Blocker Intelligence:** A deduplicated view grouping identical blockers natively while highlighting frequency, involved users, and temporal occurrence ranges.
4. **Team Rollups:** Explicit visualization tracking report statuses against organization members for specific target dates.

## Architecture & Tenancy
- Implemented using pure SQLAlchemy operations (i.e. `group_by` and `count`) bypassing external processing systems.
- Tenancy is handled safely via `deps.require_organization_member` strictly injecting `organization_id` per query.
- Role-based checking leverages `OrganizationRole.ADMIN` and `OWNER` verifying proper visibility restrictions via `.join()` schemas across user pools.
- N+1 mapping avoided via direct relationship expansion on target components.

## Frontend
The dashboard renders explicitly over standard React endpoints:
- `/daily-reports/team` (Team view)
- `/daily-reports/weekly` (Weekly aggregation charting using `recharts`)
- `/daily-reports/blockers` (Blocker intelligence matrix)
