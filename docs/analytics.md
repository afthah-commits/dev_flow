# DevFlow Analytics Architecture

Phase 6 introduces deep project and dashboard analytics.

## Core Principles
- **No Duplicate Data Storage**: Analytics are derived dynamically via `COUNT`, `SUM`, and aggregations over existing `Task` and `Project` records.
- **Actionable Metrics**: The system tracks True completion rates, status distributions, and time-based metrics.
- **Bounded External API Calls**: GitHub queries limit history tracking via strict `per_page=10` query restraints.

## Project Health Formula
The project health score is a mathematically bounded integer (0-100) reflecting stability:
1. **Base Score**: 100
2. **Overdue Penalty**: `- (overdue_tasks / total_tasks) * 40`
3. **High Priority Penalty**: `- (high_incomplete_tasks / total_tasks) * 20`
4. **Completion Bonus**: `+ (completed_tasks / total_tasks) * 20`
5. **Score Bounds**: `min(100, max(0, score))`

*Statuses*:
- 80-100: Healthy
- 50-79: Attention
- 0-49: At Risk

## Task Trends
Historical analytics simulate rolling task completions covering a standard trailing 7-day period.

## Performance Optimization
- Global statistics rely on bulk SQL `COUNT()` aggregations rather than python-level looping across thousands of active user tasks.
