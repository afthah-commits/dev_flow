# Phase 45 Verification Report — Advanced Dashboard Customization

## 1. Dashboard customization implemented

Users can personalize their dashboard without touching the analytics architecture:

- **Show/hide widgets** — checkbox toggles in a Customize panel; hidden widgets are not rendered and their data is never fetched.
- **Reorder widgets** — up/down buttons per widget in the Customize panel.
- **Save layout** — `PUT /api/v1/dashboard/layout` upserts the layout per (user, organization).
- **Restore defaults** — `DELETE /api/v1/dashboard/layout` removes the saved row and returns defaults.
- **Personal preferences** — layout is stored per user per organization; isolated between users and organizations.
- **Permission-aware widgets** — widgets with a `required_permission` are silently stripped from both reads and writes when the user lacks the permission (server-authoritative).

Frontend UI (in [Dashboard.tsx](frontend/src/pages/Dashboard.tsx)):
- `customize-button` opens `customize-panel`; `save-layout`, `cancel-customize`, `reset-layout` controls.
- Per-widget controls: `widget-toggle-<id>`, `widget-up-<id>`, `widget-down-<id>`; rendered widgets carry `widget-<id>` testids.
- Layout fetch failure falls back to defaults; after reset, the layout is re-fetched from the server.

## 2. Widgets supported

Server-authoritative `WIDGET_REGISTRY` in [dashboard.py](backend/app/api/v1/dashboard.py):

| Widget            | Required permission | Data source                          |
|-------------------|---------------------|--------------------------------------|
| `stats`           | `analytics.view`    | `/dashboard/stats`                   |
| `active_sprints`  | —                   | `/dashboard/sprints/active`          |
| `recent_projects` | —                   | existing projects query              |

Note: the `github_activity` widget from the original plan was **dropped** — the backend has only per-project GitHub analytics (`/analytics/projects/{id}/github`), no org-level endpoint, so there is no data source for an org-level widget. Only the 3 widgets above exist on both server and client.

## 3. Persistence behavior

- New model `DashboardLayout` in [dashboard.py](backend/app/models/dashboard.py): table `dashboard_layouts` with `id`, `user_id` (FK, CASCADE), `organization_id` (FK, CASCADE), `layout` (JSON), `updated_at`; unique constraint on `(user_id, organization_id)`.
- Exported via [base.py](backend/app/db/base.py) so Alembic metadata sees it.
- `GET /dashboard/layout` returns `{widgets, defaults, customized}`. `PUT` upserts. `DELETE` removes the row and returns defaults with `customized=False`.
- Sanitization on read and write (`_clean_layout`): unknown IDs, stale IDs, duplicates, and permission-gated widgets are dropped; `MAX_LAYOUT_ITEMS = 50` (51 → 422); `DEFAULT_LAYOUT = ["stats", "active_sprints", "recent_projects"]`.

## 4. Security / isolation

- All layout endpoints require auth (401 without token) and an organization header; non-members get 403.
- Permission checks are **server-side** via `_has_widget_permission` (non-raising variant of the existing `check_permission` RBAC logic in `reports.py`, including custom roles' `RolePermission` grants): OWNER/ADMIN pass all; MEMBER and custom roles are filtered by their permission list. A MEMBER saving `stats` gets it silently stripped; a custom role granted `analytics.view` can keep it.
- User isolation: user A's layout is never visible to user B in the same org. Org isolation: separate layouts per organization for the same user. Both covered by tests.
- Malformed payloads rejected with 422: `visible: {}`, `visible: [True]`, missing `id`. Missing `visible` is accepted and defaults to `true`. Pydantic laxly coerces `"yes"` → `true` (documented; pydantic default behavior, not a security issue).

## 5. Performance

- No N+1 queries: one row read/write per layout request, unique constraint upsert.
- Hidden widgets' data is **not fetched** — the frontend's conditional `Promise.all` skips those API calls entirely.
- `MAX_LAYOUT_ITEMS = 50` caps payload size; unknown/stale IDs dropped server-side, so client bugs can't bloat stored layouts.

## 6. Focused tests

**Backend** ([test_phase45_dashboard_layouts.py](backend/tests/test_phase45_dashboard_layouts.py)): **14 passed**
- 401 unauthenticated; 403 non-member; missing org header rejected
- Defaults for MEMBER (permission-filtered, no `stats`) and OWNER
- Save / load / update / reset layout
- User isolation, organization isolation
- Unknown/stale/duplicate IDs ignored (including SQL-injection-style ID string)
- Permission gating: MEMBER save silently strips `stats`; custom role with `analytics.view` grant keeps it
- Malformed payloads → 422; size limit 51 → 422, 50 OK

**Frontend** ([DashboardCustomize.test.tsx](frontend/src/pages/DashboardCustomize.test.tsx)): **10 passed**
- Defaults render, customize panel open/close, toggle visibility, reorder up/down
- Save sends the full draft; cancel discards changes
- Reset restores defaults and re-fetches (stateful `getLayout` mock: stale layout before reset, defaults after — matching real component behavior)

## 7. Full backend tests

`python -m pytest tests -q` from `backend/`: **281 passed, 4 failed** (237s).

The 4 failures are the known **pre-existing** phase 38–40 route-pin tests (confirmed failing on a clean checkout with `git stash` during Phase 44 verification):
- `test_phase38_analytics.py::test_delivery_and_dora_registered_on_analytics_router`
- `test_phase39_analytics_clients.py::test_project_github_route_registered_once`
- `test_phase40_github_reliability.py::test_frontend_analytics_time_urls_exist_in_backend`
- `test_phase40_github_reliability.py::test_github_analytics_route_registered_exactly_once`

They are environment artifacts (`app.routes` pin checks) unrelated to Phase 45. Not weakened, not skipped.

## 8. Frontend tests

`npx vitest run` from `frontend/`: **15 files / 77 tests passed** (exit 0), including the 10 new Phase 45 tests.

## 9. TypeScript / build

- `npx tsc --noEmit`: clean (exit 0).
- `npm run build`: success in 4.7s. Pre-existing chunk-size warning and `INEFFECTIVE_DYNAMIC_IMPORT` notice for `sprintApi.ts` (unrelated to this phase).

## 10. Migration status

- Migration [b2c3d4e5f6a7_phase45_dashboard_layouts.py](backend/alembic/versions/b2c3d4e5f6a7_phase45_dashboard_layouts.py) (`b2c3d4e5f6a7`, down_revision `a1b2c3d4e5f6` = Phase 44's revision).
- **Cycle verified on `devflow.db`**: downgrade to `a1b2c3d4e5f6` → table gone → upgrade to head → `b2c3d4e5f6a7 (head)`; columns `id/user_id/organization_id/layout/updated_at` confirmed.
- **Pre-existing limitation (documented, not fixed — out of scope):** a fresh-DB `alembic upgrade head` fails at migration `d36b2909d14d_phase_32_release_models.py`, which unconditionally `op.drop_table('_alembic_tmp_attachments')` — the table doesn't exist on a fresh DB (`sqlite3.OperationalError: no such table`). This bug predates Phase 44/45 (it's why `devflow.db` was stuck at `d4e5f6a7b8c9` earlier); the test database uses `Base.metadata.create_all`, so tests are unaffected.

## 11. Commit hash

Single commit on `master`: see `git log -1` — `feat: add customizable dashboard layouts`. Only Phase 45 files staged; the unrelated pre-existing `frontend/src/lib/searchApi.ts` edit (leftover from Phase 43) was explicitly **excluded** from the commit and left uncommitted in the working tree.

## 12. Remaining limitations

1. `github_activity` widget omitted — no org-level GitHub analytics endpoint exists; would require a new endpoint in a later phase if wanted.
2. Fresh-DB Alembic upgrade blocked by the pre-existing `d36b2909d14d` migration bug (see §10).
3. 4 pre-existing phase 38–40 route-pin test failures remain (see §7).
4. Pydantic lax coercion of `visible` (e.g. `"yes"` → `true`) — accepted pydantic default, low risk.
5. No drag-and-drop reorder — up/down buttons only, per "no over-engineering" constraint.
6. Layout versioning/migration: layout JSON is stored as-is and sanitized on read; unknown widget IDs from future versions are simply dropped.
