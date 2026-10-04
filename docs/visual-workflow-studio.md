# Visual Workflow Studio (Phase 30)

Phase 30 upgrades the Phase 29 structured Workflow Builder into a professional
visual Workflow Studio with an infinite canvas, validation gate, dry-run
simulator, advanced form builder, immutable versioning, execution history, and
an advisory AI design assistant.

## Architecture

```
frontend/
  src/pages/WorkflowStudio.tsx        # Studio shell: canvas + panels + modals
  src/pages/WorkflowFormBuilder.tsx   # /workflows/:id/forms — drag-and-drop form builder
  src/pages/Workflows.tsx             # Workflow list + creation
  src/pages/WorkflowAnalytics.tsx     # Recharts analytics dashboard
  src/lib/workflowApi.ts              # Typed API client (org-scoped)
backend/
  app/services/workflow_studio.py     # Validation, simulation, versioning, execution engine
  app/services/workflow_permissions.py# Phase 17 RBAC bridge (workflows.* permissions)
  app/api/v1/workflows.py             # REST endpoints (Phase 29 + Phase 30)
  app/models/workflow.py              # + WorkflowVersion, WorkflowStateLayout, state_type, approval_config
  alembic/versions/b3f0a9c17d30_phase30_workflow_studio.py
backend/tests/test_workflow_studio.py # 25 Phase 30 tests
frontend/src/pages/WorkflowStudio.test.tsx  # 5 frontend tests
```

The canvas is dependency-free: plain React + SVG bezier edges + absolutely
positioned HTML nodes. No React Flow / XFlow / DnD library was added.

## Workflow lifecycle (versions)

```
DRAFT ──publish──▶ PUBLISHED ──archive──▶ ARCHIVED (readable forever)
  ▲                    │
  └── new snapshot ────┘   (publishing vN archives the previous published version)
```

- Editing a **published** workflow never mutates the published snapshot; the
  live graph is the editable draft and `Save Draft` / `Publish` snapshots it
  into a new `WorkflowVersion` row.
- Published versions are **immutable** — no endpoint mutates a version row.
- `WorkflowExecution.workflow_version_id` pins every execution to the version
  it started against; re-publishing does not rewrite history.
- Publishing runs the validation gate server-side; critical errors return
  HTTP 400 with the full validation report and nothing is published.

## Visual editor

Route: `/workflows/:workflowId/studio`

- **Canvas**: pan (drag background), zoom (Ctrl+wheel and +/− buttons), grid
  background, fit-to-view, minimap, drag nodes, save/reset layout
  (`workflow_state_layouts` table).
- **Nodes** show name, state type badge, incoming/outgoing counts, approval
  indicator, action indicator, and validation-warning markers.
- **Link mode**: click a node's `→` handle, then click a target state to
  create a transition.
- **Left sidebar**: States / Transitions lists plus view tabs
  (canvas, forms, versions, executions).
- **Right sidebar**: selected state or transition configuration —
  name, description, color, state type, initial/final, approval config,
  conditions (safe operators), ordered actions with enable/disable.
- **Bottom panel**: validation report and simulation results.

## Validation

`POST /api/v1/workflows/{id}/validate` returns PASS / WARNING / ERROR issues:

| Severity | Checks |
|---|---|
| ERROR (blocks publish) | no states, no initial state, multiple initial states, no final state, duplicate state names/keys, broken transitions, self-transitions, invalid condition operator/missing field/missing numeric value, invalid action configuration (CREATE_TASK title, SEND_NOTIFICATION message, TRIGGER_AUTOMATION automation_id, CREATE_AUDIT_EVENT event_type), invalid approval config, missing form labels, unsafe visibility operators |
| WARNING | unreachable states, dead-end states (non-terminal, no outgoing), circular transitions that can never reach a terminal state, approval requested without config |
| PASS | explicit confirmations (initial/final configured, transitions valid, forms valid) |

## Simulation (dry-run)

`POST /api/v1/workflows/{id}/simulate` walks the graph with a safe condition
evaluation against sample data:

```
Current State → Condition evaluation → Transition → Actions (WOULD_RUN) → Next State
```

Guarantees:
- Never writes `WorkflowExecution`, entities, or action side effects.
- Actions are enumerated with `dry_run: true` / status `WOULD_RUN`.
- Stops at approval gates (`BLOCKED`), failed conditions (`FAIL`), dead ends,
  or after 50 steps (cycle guard).
- The only database write is the `workflow.simulation_started` audit event.

## Forms

Route: `/workflows/:workflowId/forms`

16 field types (TEXT, TEXTAREA, NUMBER, DATE, DATETIME, SELECT, MULTI_SELECT,
CHECKBOX, RADIO, USER, TEAM, PROJECT, TASK, CLIENT, FILE, CUSTOM_FIELD) with
label, description, required, default value, placeholder, position, width,
options, validation rules, and conditional visibility rules.

- Field definitions live in `WorkflowForm.configuration` (existing JSON column);
  `CUSTOM_FIELD` type links to existing `CustomField` rows — no duplicated
  storage.
- Visibility rules run through the existing safe condition engine
  (`EQUALS … IS_NOT_EMPTY`), enforced server-side; `eval()` is never used.
  `evaluate_form_visibility()` computes visible fields for a set of answers.

## AI assistant (advisory only)

`POST /api/v1/ai/workflows/generate` returns an `AIWorkflowSuggestion` with
states, transitions, conditions, actions, approvals, and form fields derived
deterministically from the prompt.

Safety invariants (tested):
- The generate endpoint **never** writes workflow rows — only a
  `workflow.ai_suggestion_generated` audit event.
- The user must explicitly call `POST /api/v1/workflows/ai/apply`, which
  creates a **draft** workflow (`is_active=False`), never a published one.
- Unsafe operators/action types from the suggestion are dropped during apply.
- Publishing still requires human validation + publish actions.

The studio UI shows: "⚠ AI-generated suggestion — review before applying."

## Realtime (Phase 23/24)

Broadcast over the existing org websocket manager, applied via
`useRealtimeEvent` subscriptions (no page reloads):

`workflow.updated`, `workflow.published`, `workflow.archived`,
`workflow.execution.started`, `workflow.execution.completed`,
`workflow.execution.failed`.

## Audit logging

`record_event` with metadata sanitization (reuses `audit_service` redaction):

`workflow.created`, `workflow.updated`, `workflow.version_created`,
`workflow.published`, `workflow.archived`, `workflow.state_created`,
`workflow.state_updated`, `workflow.state_deleted`,
`workflow.transition_created`, `workflow.transition_updated`,
`workflow.transition_deleted`, `workflow.execution_started`,
`workflow.execution_completed`, `workflow.execution_failed`,
`workflow.simulation_started`, `workflow.form_created`,
`workflow.form_updated`, `workflow.form_deleted`, `workflow.layout_saved`,
`workflow.layout_reset`, `workflow.ai_suggestion_generated`.

Passwords, tokens, API keys, and secrets are never logged (shared redaction).

## Security & RBAC

- Every endpoint requires `X-Organization-Id` and validates organization
  membership (`require_organization_member`).
- `get_workflow_permission` enforces Phase 17 custom-role permissions:
  `workflows.view`, `workflows.create`, `workflows.update`,
  `workflows.delete`, `workflows.publish`, `workflows.execute`,
  `workflows.simulate`, `workflows.manage_forms`.
  OWNER/ADMIN pass; custom roles need the explicit grant; MEMBER falls back to
  the Phase 29 defaults (view/execute/simulate only).
- Cross-organization reads/writes return 403/404 (tested).
- Execution start verifies the target entity belongs to the caller's org.
- Client-portal users never see internal workflow management endpoints.

## API reference (Phase 30 additions)

```
GET    /api/v1/workflows/{id}/studio
POST   /api/v1/workflows/{id}/validate
POST   /api/v1/workflows/{id}/simulate
GET    /api/v1/workflows/{id}/versions
POST   /api/v1/workflows/{id}/versions
GET    /api/v1/workflows/{id}/versions/{version_id}
POST   /api/v1/workflows/{id}/publish
POST   /api/v1/workflows/{id}/archive
GET    /api/v1/workflows/{id}/executions
GET    /api/v1/workflows/{id}/executions/{execution_id}
POST   /api/v1/workflows/{id}/executions
GET    /api/v1/workflows/{id}/forms
POST   /api/v1/workflows/{id}/forms
PATCH  /api/v1/workflows/{id}/forms/{form_id}
DELETE /api/v1/workflows/{id}/forms/{form_id}
POST   /api/v1/workflows/{id}/states | PATCH/DELETE /{state_id}
POST   /api/v1/workflows/{id}/transitions | PATCH/DELETE /{transition_id}
POST   /api/v1/workflows/{id}/layout | /layout/reset
GET    /api/v1/workflows/{id}/analytics
POST   /api/v1/workflows/ai/apply
POST   /api/v1/ai/workflows/generate   (upgraded, preview-only)
```

## Migration

`b3f0a9c17d30_phase30_workflow_studio` (down_revision `70994c719dcd`):

- New tables: `workflow_versions`, `workflow_state_layouts`
- New columns: `workflow_states.state_type/approval_config`,
  `workflow_transitions.description/approval_config`,
  `workflow_executions.workflow_version_id/trigger_source/error_message`

Purely additive with `server_default='NORMAL'` — safe for SQLite
(`batch_alter_table`) and PostgreSQL. Verified upgrade → downgrade → upgrade
roundtrip on a populated database; no existing rows deleted.

## Testing

- Backend: `backend/tests/test_workflow_studio.py` — 25 tests covering tenant
  isolation, RBAC, validation, state/transition CRUD, invalid transition
  rejection, simulation dry-run, publishing gate, version immutability,
  approval configuration, form validation, conditional visibility, AI preview
  safety, execution isolation, layout, audit, analytics.
- Frontend: `frontend/src/pages/WorkflowStudio.test.tsx` — 5 tests covering
  canvas rendering, validation panel, published badge, versions tab, and the
  workflow list.
