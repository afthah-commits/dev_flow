# Notifications & Action Center

> Phase 36 — Advanced Notifications & Action Center.
> Extends the existing in-app notification, realtime/WebSocket, RBAC and
> organization-isolation infrastructure. No new queue, no external notification
> service, no new WebSocket implementation.

## Contents

- [Architecture](#architecture)
- [Notification types](#notification-types)
- [Event sources](#event-sources)
- [Deduplication](#deduplication)
- [Realtime delivery](#realtime-delivery)
- [Action Center](#action-center)
- [RBAC](#rbac)
- [Tenant isolation](#tenant-isolation)
- [Preferences](#preferences)
- [GlobalSearch](#globalsearch)
- [Performance](#performance)
- [Database](#database)
- [API reference](#api-reference)
- [Frontend](#frontend)
- [Testing](#testing)

---

## Architecture

Phase 36 **extends** the existing notification stack rather than adding a
parallel one:

```
domain event (API / service / scheduler)
        │
        ▼
app/services/notification_service.py   ← preference gate + dedup + fan-out
        │
        ▼
app/services/channels.py  (NotificationDispatcher)
        ├── InAppNotificationChannel  → notifications row + WebSocket emit
        └── EmailNotificationChannel  → placeholder (unchanged, no external service)
        │
        ▼
GET /api/v1/notifications*            ← backend-driven filters, pagination, RBAC
        │
        ▼
NotificationCenter (badge) · NotificationsPage · ActionCenter
```

Nothing new was introduced for transport: the pre-existing
`app/websockets/manager.py` `ConnectionManager` is reused for both the personal
`notification.created` event and the org-scoped `action_item.created` event.

### Reused, not duplicated

| Existing capability | Phase 36 use |
| --- | --- |
| `Notification` / `NotificationPreference` models | extended in place — **no new table** |
| `NotificationDispatcher` / `InAppNotificationChannel` | single write path for every new notification |
| `ConnectionManager` (`send_personal_message`, `broadcast_to_org`) | realtime fan-out |
| `useRealtime` / `useRealtimeEvent` (frontend) | UI refresh without reload |
| `OrganizationMember` | recipient resolution + preference lookup |
| `AuditEvent` | untouched; events are still audited separately |
| RBAC `deps.require_organization_member` | unchanged enforcement |
| Alembic | one new migration for the added columns |

---

## Notification types

All categories named in the Phase 36 brief are deterministic constants on
`app.models.notification.NotificationType`:

```
DAILY_REPORT_REMINDER      DAILY_REPORT_BLOCKER
RELEASE_APPROVAL_REQUESTED RELEASE_APPROVED  RELEASE_REJECTED
RELEASE_PROMOTED           RELEASE_ROLLBACK
DEPLOYMENT_STARTED         DEPLOYMENT_SUCCESS DEPLOYMENT_FAILED
DEPLOYMENT_ROLLBACK
JOB_FAILURE                AUTOMATION_FAILURE
WORKFLOW_APPROVAL_REQUESTED WORKFLOW_APPROVED WORKFLOW_REJECTED
CLIENT_REQUEST_CREATED     CLIENT_REQUEST_UPDATED
TEAM_ACTIVITY
```

Pre-existing Phase 1–35 types (`TASK_OVERDUE`, `TASK_DUE_SOON`,
`PROJECT_DEADLINE`, `PROJECT_AT_RISK`, `GITHUB_*`, `AI_INSIGHT`, and the legacy
`JOB_FAILED` written by the scheduler) are unchanged.

`NotificationType` values equal their own names — asserted by
`test_notification_types_are_deterministic_and_supported`.

---

## Event sources

Notifications are only created when the corresponding real event fires. Each
call site is wrapped in `try/except` so notification plumbing can never break
the business transaction it observes.

| Event | Type | Recipients | Call site |
| --- | --- | --- | --- |
| Daily report submitted with blockers | `DAILY_REPORT_BLOCKER` | all org members | `api/v1/daily_reports.py` → `notify_daily_report_blocker` |
| Missing daily report (current user, today) | `DAILY_REPORT_REMINDER` | the user | lazy check in `GET /notifications` → `check_and_generate_daily_report_reminder` |
| Release approval requested | `RELEASE_APPROVAL_REQUESTED` | requested reviewer | `api/v1/delivery.py` → `notify_release_approval_requested` |
| Release approved / rejected | `RELEASE_APPROVED` / `RELEASE_REJECTED` | requester | `api/v1/delivery.py` → `notify_release_decision` |
| Release promoted | `RELEASE_PROMOTED` | all org members | `api/v1/delivery.py` → `notify_release_event` |
| Release rolled back | `RELEASE_ROLLBACK` | all org members | `api/v1/delivery.py` → `notify_release_event` |
| Deployment started / succeeded | `DEPLOYMENT_STARTED` / `DEPLOYMENT_SUCCESS` | all org members | `api/v1/deployments.py` → `notify_deployment_event` |
| Deployment failed | `DEPLOYMENT_FAILED` | all org members | `api/v1/deployments.py` → `notify_deployment_failed` |
| Job permanently failed (retries exhausted) | `JOB_FAILURE` | org members without an existing notice | `jobs/scheduler.py` → `notify_job_failure` |
| Automation execution failed | `AUTOMATION_FAILURE` | all org members | `services/automation_engine.py` → `notify_automation_failure` |
| Workflow approval created | `WORKFLOW_APPROVAL_REQUESTED` | the approver | `services/workflow_studio.py` → `notify_workflow_approval_requested` |
| Client request created | `CLIENT_REQUEST_CREATED` | all org members | `services/client_service.py` → `notify_client_request` |
| Task assigned to someone else | `TEAM_ACTIVITY` | the assignee | `api/v1/tasks.py` → `notify_team_activity` |

### Daily report reminder — determinism rules

`check_and_generate_daily_report_reminder` deliberately does **not** fire for
every user. It only creates a reminder when **both** hold:

1. the user has submitted at least one `DailyReport` in the last 30 days
   (they are an actual reporter), **and**
2. they have no `DailyReport` row for today.

Non-reporters are never spammed, and the 24-hour dedup window in
`create_notification` guarantees at most one reminder per user per day.

### Not deliberately wired

Workflow execution failures, deployment rollbacks and release "promoted" noise
are **not** emitted for every internal state change — only the meaningful,
user-actionable transitions listed above. `AUTOMATION_FAILURE` is emitted once
per failed execution, not once per failed action.

---

## Deduplication

`create_notification` performs a lookup **before** inserting. Within a rolling
24-hour window it refuses to create a second row for the same:

- `user_id` + `type` + (`entity_type`, `entity_id`) when the entity is known, or
- `user_id` + `type` + `title` otherwise.

It returns `True` on create and `None` when deduplicated, so callers can be
idempotent.

Two extra guards exist for overlapping sources:

- **`notify_job_failure`** skips any user who already has *any* notification for
  that `entity_id` in the last 24h. The scheduler writes its own legacy
  `JOB_FAILED` notice for owners/admins (Phase 31 contract, still asserted by
  `test_phase31_jobs.py`), so Phase 36 never doubles it up.
- **`notify_client_request` / release decisions** are keyed on the entity, so a
  retried or re-sent request cannot produce a duplicate.

---

## Realtime delivery

Event names follow the convention the brief suggested, and the existing
`useRealtimeEvent` subscription mechanism:

| Event | Scope | Emitted from |
| --- | --- | --- |
| `notification.created` | personal (owning user) | `channels.py::InAppNotificationChannel` |
| `notification.read` | personal | `PATCH /notifications/{id}/read` |
| `notification.read_all` | personal | `POST/ PATCH /notifications/read-all` |
| `notification.updated` | personal | unread / important / unimportant |
| `notification.deleted` | personal | `DELETE /notifications/{id}` |
| `action_item.created` | organization | `channels.py` when `action_required=True` |

Every emission is fire-and-forget and wrapped in `try/except`: if no WebSocket
loop is available (e.g. a background thread or a plain request), the
notification is still persisted and nothing raises.

Consumers:

- `NotificationCenter` badge refreshes on `notification.created`,
  `.read`, `.updated`, `.deleted`, `.read_all`.
- `NotificationsPage` reloads the current filter page on `notification.created`.
- `ActionCenter` reloads on `action_item.created` **and** `notification.created`.

No second WebSocket implementation was added.

---

## Action Center

`GET /api/v1/notifications/action-center` is an **aggregation layer only** — it
reads existing business objects and never creates, mutates or duplicates them.

Sources, in priority order:

1. **Pending workflow approvals** assigned to the current user (`WorkflowApproval`)
2. **Pending release approvals** in the user's organizations (`ReleaseApproval`)
3. **Failed jobs** in the user's organizations (`Job.status == FAILED`)
4. **Failed deployments** in the user's organizations (`Deployment.status == FAILED`)
5. **Daily reports with blockers** in the last 7 days (`DailyReport.blockers`)
6. **Action-required, unread notifications** for the current user

Each item carries `title`, `description` (the reason / action required),
`entity_type`, `entity_id`, `priority`, `created_at` and an `action_url` for
one-click navigation (e.g. `Deployment failed → /infrastructure/deployments/{id}`).

Results are sorted by priority (`URGENT → HIGH → NORMAL → LOW`) then newest
first. Each source is capped at 20 items (50 for reports) so the endpoint can
never load a whole table.

`GET /api/v1/notifications/summary` returns SQL `count()` aggregates:
`unread`, `important`, `action_required`, `pending_approvals`, `failed_jobs`.

### Deployment labelling

`Deployment` has **no `name` column and no `updated_at` column**. A first draft
referenced `dep.name` / `dep.updated_at`, which was swallowed by the source's
`try/except` and silently produced zero deployment items. `_deployment_label()`
now derives a label from `deployment_key → version → commit_sha → id`, and
ordering uses `created_at`. This is covered by an explicit integration check
(`AGGREGATION=PASS all 6 sources produced items`).

---

## RBAC

- Every `/api/v1/notifications*` route requires `deps.get_current_user`
  (401 without a token) — asserted by `test_notifications_require_authentication`.
- The Action Center and summary endpoints additionally resolve the caller's
  organizations through `OrganizationMember`; non-members see nothing from an
  org they do not belong to.
- Every per-notification mutation (`GET/{id}`, `read`, `unread`, `important`,
  `unimportant`, `DELETE`) filters on `user_id == current_user.id` and returns
  **404** for a foreign id — never 403, so ids are not confirmed to exist.
- Malformed and random UUIDs return 404/422, never 500.

---

## Tenant isolation

- `notifications.organization_id` (nullable, indexed, `ON DELETE CASCADE`)
  records the owning organization for every org-scoped event.
- Listing, summary and Action Center queries are always constrained to
  `current_user.id` **and** to the caller's organization set.
- Realtime `action_item.created` uses `broadcast_to_org`, so an org never
  receives another org's action items; `notification.*` events use
  `send_personal_message`, so they reach exactly one user.
- GlobalSearch notification results are constrained to
  `user_id == current_user.id` **and**
  `organization_id == org_id OR organization_id IS NULL`.

Legacy rows created before Phase 36 have `organization_id IS NULL`; they are
still owned by their user and remain visible to that user only.

---

## Preferences

`NotificationPreference` was **extended** (same table, same primary key) with
eight new columns:

```
daily_report_notifications   deployment_notifications
release_notifications        job_notifications
automation_notifications     workflow_approval_notifications
client_request_notifications team_activity_notifications
```

All default to `True` and are applied at **generation time**: the service
checks the recipient's preference before creating a row, so opted-out users
simply never receive that category (they are not created-then-hidden).

Toggles are exposed at `/settings/notifications` and via
`GET`/`PATCH /api/v1/notifications/preferences`.

---

## GlobalSearch

The existing `GET /api/v1/search` is a flat, org-scoped `ilike` aggregator
returning `DOCUMENT / PROJECT / TASK / DISCUSSION` hits. Notifications were
added as a fifth block **without any architectural change**: it is one extra
`LIMIT 5` query, user-scoped, returning `entity_type: "NOTIFICATION"` with
`url: "/notifications"`. No redesign of GlobalSearch was required, so it was
otherwise left untouched.

---

## Performance

- Listing uses **offset/limit pagination** with `limit` capped at 200.
- All filters (`priority`, `unread_only`, `entity_type`, `notification_type`,
  `important`, `action_required`, `date_from`, `date_to`) are applied **in
  SQL** — the frontend never receives the full table to filter client-side.
- Summary counts use SQL `count()` aggregation, not Python iteration.
- No N+1: each Action Center source issues one query; there is no per-row
  follow-up query.
- Indexed columns: `notifications.user_id`, `.type`, `.read`, `.action_required`,
  `.important`, `.organization_id`, `.entity_type`, `.entity_id`, `.created_at`.
- Recipient fan-out (`get_org_member_user_ids`) is a single query; preference
  lookups reuse `get_preferences`, which creates on first access.
- Action Center sources are individually limited (20 / 20 / 20 / 20 / 50 / 20).

---

## Database

Migration `86f704f37613_add_advanced_notifications_fields.py`
(revises `b27b8e7e4ff4`):

**`notifications`** — adds `organization_id` (nullable UUID FK →
`organizations.id`, `ON DELETE CASCADE`), `action_required` (bool, default 0),
`important` (bool, default 0), plus indexes on all three.

**`notification_preferences`** — adds the eight boolean columns above with
`server_default='1'` so existing rows keep working.

Built with `op.batch_alter_table` so it works on SQLite for local development.
Existing notification rows are preserved — no table is recreated and no data is
dropped. Validated with a real upgrade → downgrade → upgrade cycle:

```
HEAD: 86f704f37613
--- upgrade head ---      OK
--- downgrade -1 ---      OK
--- upgrade head again --- OK
MIGRATION_CYCLE=PASS
```

---

## API reference

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/notifications` | list + filter + paginate |
| `GET` | `/api/v1/notifications/unread-count` | badge count |
| `GET` | `/api/v1/notifications/summary` | aggregated counts |
| `GET` | `/api/v1/notifications/action-center` | aggregated action items |
| `POST`/`PATCH` | `/api/v1/notifications/read-all` | mark all read |
| `GET`/`PATCH` | `/api/v1/notifications/preferences` | read/update preferences |
| `GET` | `/api/v1/notifications/{id}` | single notification |
| `PATCH` | `/api/v1/notifications/{id}/read` | mark read |
| `PATCH` | `/api/v1/notifications/{id}/unread` | mark unread |
| `PATCH` | `/api/v1/notifications/{id}/important` | mark important |
| `PATCH` | `/api/v1/notifications/{id}/unimportant` | unmark important |
| `DELETE` | `/api/v1/notifications/{id}` | delete |

Static paths are declared **before** `/{notification_id}` so FastAPI does not
shadow them. `GET` accepts `priority`, `unread_only`, `entity_type`,
`notification_type`, `important`, `action_required`, `date_from`, `date_to`,
`skip`, `limit`.

---

## Frontend

| File | Role |
| --- | --- |
| `pages/NotificationsPage.tsx` | `/notifications` — tabs (All / Unread / Important / Action Required), type filter, date range, server pagination, per-item read/unread/important/delete |
| `pages/ActionCenter.tsx` | `/action-center` — summary tiles + grouped action items with "Open →" navigation |
| `components/NotificationCenter.tsx` | header dropdown, live unread badge, quick filters |
| `pages/NotificationPreferences.tsx` | all preference toggles including the eight new categories |
| `lib/notificationApi.ts` | typed API client |
| `types/notification.ts` | `Notification`, `NotificationPreference`, `NotificationSummary`, `ActionItem` |

Both routes are registered in `App.tsx` under the dashboard layout and linked
from `DashboardLayout.tsx`. Styling uses the existing Tailwind design system
only — no new UI library.

---

## Testing

`backend/tests/test_phase36_notifications.py` — 22 tests covering:
creation, dedup/idempotency, preference gating, per-category generation,
org scoping of created rows, realtime personal/org scoping, authentication
requirements, listing + every backend filter + pagination, read/unread/mark-all,
important state, summary counts, Action Center aggregation and ordering,
cross-user 404s for every mutation, malformed/random ids, preference round-trip,
type determinism, and GlobalSearch visibility.

An additional standalone check
(`backend/run_phase36_actioncenter_check.py`) proves all six Action Center
sources actually return items against a real session.

> **Note on a pre-existing test defect:** `backend/tests/api/v1/*.py` register
> `app.dependency_overrides[deps.get_current_user]` at module import time and
> never remove it, so any test collected after them silently bypasses
> authentication. The Phase 36 suite clears those leaked overrides for its own
> duration (via an autouse fixture) and restores them afterwards, so other
> suites are unaffected. This is a test-infrastructure issue, not an
> application one — production has no such override.
