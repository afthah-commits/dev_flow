"""Phase 31 — add missing query-pattern indexes.

Reconciles two kinds of drift found during the Phase 31 index review:

1. Model declarations that no migration ever created
   (projects.key, sprints.key carry index=True in the models but the
   migrated database has no matching index).
2. Hot query paths that had no index at all:
   - workflow_executions.status      (execution history filters)
   - login_events.organization_id    (org-scoped security listing)
   - client_requests.status          (client portal status filters)
   - time_entries.started_at         (time report date ranges)
   - notifications.read              (unread-count badge)

Uses CREATE INDEX IF NOT EXISTS / DROP INDEX IF EXISTS, which both SQLite
and PostgreSQL (9.5+) support, so the migration is idempotent and safe to
re-run. sprints.key is created as a NON-unique index: the model declares
unique=True, but retroactively enforcing uniqueness on existing data is a
data-repair decision, not a schema migration — existing rows are never
altered by this migration.

Revision ID: d4e5f6a7b8c9
Revises: b3f0a9c17d30
Create Date: 2026-10-05
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "b3f0a9c17d30"
branch_labels = None
depends_on = None

INDEXES = [
    ("ix_workflow_executions_status", "workflow_executions", "status"),
    ("ix_login_events_organization_id", "login_events", "organization_id"),
    ("ix_client_requests_status", "client_requests", "status"),
    ("ix_time_entries_started_at", "time_entries", "started_at"),
    ("ix_notifications_read", "notifications", "read"),
    ("ix_projects_key", "projects", "key"),
    ("ix_sprints_key", "sprints", "key"),
]


def upgrade() -> None:
    for name, table, column in INDEXES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})")


def downgrade() -> None:
    for name, _table, _column in reversed(INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {name}")
