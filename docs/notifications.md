# DevFlow Notification System

Phase 6 implements a comprehensive, deduplicated Notification engine.

## Infrastructure
- **Models**: `Notification`, `NotificationPreference`
- **Routing**: `api/v1/notifications` handles CRUD and reading operations.

## Notification Generation
Notifications are instantiated via specific business rules evaluated inside `app/services/notification_service.py`.

Current generation triggers:
1. `check_and_generate_overdue_notifications`:
   - Checks tasks with `due_date < now` (`TASK_OVERDUE`)
   - Checks tasks due within 48 hours (`TASK_DUE_SOON`)
2. `check_and_generate_health_notifications`:
   - Scans projects resolving to `At Risk` statuses. (`PROJECT_AT_RISK`)

## Deduplication Strategy
To prevent spam, DevFlow suppresses identical notifications within a rolling 24-hour window per user using cryptographic constraints:
- Matches `user_id` + `notification_type` + `title` within `now() - timedelta(hours=24)`.

## Preferences
Every user receives a unique `NotificationPreference` record enforcing opt-out capabilities on specific categories (e.g. `deadline_notifications`, `ai_notifications`).

## UI Integration
- **NotificationCenter**: A real-time dropdown bell icon rendering active unread counts.
- **Lazy loading**: Evaluates notifications passively during layout mount phases to prevent heavy synchronous API lockouts.
