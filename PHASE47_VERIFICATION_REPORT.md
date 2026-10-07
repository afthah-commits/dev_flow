# Phase 47 Verification Report — AI-Assisted Planning & Estimation

## 1. Feature summary

Advisory AI planning for a project or any single task, integrated into the existing AI/Project Intelligence experience:

- **Analyze** button → planning summary (complexity, effort estimate + confidence, risks, missing info, dependency concerns, sprint capacity, suggested task breakdown).
- **Breakdown suggestions** are preview-only checkboxes; user selects and explicitly presses **Apply Selected** — only selected suggestions are created, as subtasks of the analyzed task, in one transaction, audited.
- Cancel discards everything; nothing is created without the explicit Apply click. The AI response itself can never trigger mutations.
- New files: [planning.py](backend/app/services/ai/planning.py) (service), [ProjectAIPlanning.tsx](frontend/src/components/ProjectAIPlanning.tsx) (UI), tests on both sides. Endpoints added in [ai.py](backend/app/api/v1/ai.py); UI mounted at the top of the existing `ProjectIntelligence` panel (no page redesign).

## 2. AI planning behavior

`POST /api/v1/ai/projects/{project_id}/planning/analyze` (body `{task_id?}`):

- Deterministic heuristics compute complexity (LOW/MEDIUM/HIGH from description length, checklist count, blocking dependencies, priority), risks (overdue, blockers, high-complexity-with-no-checklist), missing information (assignee/due date/manual estimate/description), and dependency concerns (unfinished blockers listed with keys).
- Suggested breakdown goes through the **existing** `AIProvider` abstraction using the reused `subtasks` JSON contract that MockAIProvider already serves — fully deterministic in tests. Output is strictly sanitized: plain strings only, priority coerced to LOW/MEDIUM/HIGH/CRITICAL (default MEDIUM), titles ≤200 chars, descriptions ≤1000, max 8 suggestions.
- Auth required; project 404; task must belong to the project (404) and its organization (403); org membership enforced everywhere.

## 3. Estimation logic

Story points — the existing `Task.estimate_points` convention (also used by Sprint snapshots and capacity analytics). Base by complexity (2/5/8) + subtask count + blocker count, capped at 21. Confidence: HIGH if a manual estimate already exists, MEDIUM if a description exists, LOW otherwise; factors listed explicitly. Clearly labeled AI-assisted/advisory ("not historical truth" shown in UI). Unit convention already existing in DevFlow was preferred; no new estimation framework.

## 4. Task breakdown

Provider-generated suggestions (e.g. "Implement payment integration" → provider configuration / backend service / webhook handling / etc. via MockAIProvider's deterministic subtasks). Preview-only; checkboxes select/unselect; **Apply Selected** creates only the selected ones as `Task` rows with `parent_id` set, generated `task_key` (`{project.key}-{seq}` / `PROJ-{seq}`), sanitized priority, creator = requesting user.

## 5. Sprint capacity

Reuses existing sprint data — `Sprint.capacity` plus non-done sprint tasks' `estimate_points` (single aggregate query, no N+1). Shows capacity / committed / remaining with OVER_CAPACITY warning (also surfaced as a risk). Missing sprint or capacity → `INSUFFICIENT_DATA` (rendered "Insufficient data"); no invented values, no second capacity engine.

## 6. Apply/preview safety

- `POST /api/v1/ai/projects/{project_id}/planning/apply` (body `{task_id, suggestions[]}`) — **explicit user action only**; empty selection → 422; blank title → 422; >8 → 422; unknown priority silently coerced to MEDIUM (never stored raw, never interpreted).
- Permissions re-validated server-side at apply time (auth + org membership + project/task ownership). AI response content cannot invoke mutations.
- Transactional: all selected suggestions are created in a single `db.commit()`; on failure rollback → nothing created. Response reports applied count, task ids and keys.
- Audit: `ai.planning_analyzed` (analyze) and `ai.planning_applied` with created count/keys (apply) via the existing `record_event` service; verified in tests.

## 7. Security

- 401 without token; org membership via `require_organization_member` / `require_current_organization_id`; foreign project → 403/404; foreign task under own project → 404 (verified).
- Rate-limited like other AI endpoints (`AI_RATE_LIMIT` reuse).
- Prompt injection: untrusted task text is bounded (500 chars), the system prompt retains the existing "UNTRUSTED CONTEXT" guard, suggestions come back only through the strict sanitizer — no executable configuration is possible (plain `{title, description, priority}` objects only). Injection test asserts no PWNED tasks, no SQL, no role escalation.
- AI never bypasses RBAC: the planning code path uses the same deps/RBAC endpoints as everything else.

## 8. Performance

- No N+1: one count query per relation (dependencies, checklist relationship, subtasks relationship), and one aggregate for sprint tasks; task/project resolved with indexed PK lookups.
- No external AI service required (MockAIProvider default), no background worker, no polling, no Redis, bounded suggestion count (8) and text lengths.

## 9. Backend tests

Focused [test_phase47_ai_planning.py](backend/tests/test_phase47_ai_planning.py): **13 passed** — analyze round-trip + deterministic repeat (identical breakdown/complexity), 401/404s, complexity & risk & dependency detection, estimate confidence levels + missing-info, sprint capacity OK/OVER_CAPACITY/INSUFFICIENT_DATA, org isolation + foreign ids, prompt injection, preview non-mutation, apply creates only selected subtasks transactionally (parents/keys/creator asserted), invalid/empty/oversized selection 422, priority coercion, foreign-id apply creates nothing, audit events, non-member 403.

Full backend suite once: **299 passed, 4 failed** (Phase 46 baseline 286/4 + 13 new; the same 4 pre-existing phase 38–40 route-pin failures, untouched).

## 10. Frontend tests

Focused [ProjectAIPlanning.test.tsx](frontend/src/components/ProjectAIPlanning.test.tsx): **11 passed** — panel renders with tasks, loading state, estimate/confidence/complexity display, risk display, suggestion select/unselect (apply sends only selected), apply disabled when none selected, no auto-mutation on analyze, cancel discards, error state, sprint capacity + insufficient-data handling, project-level (no task) apply disabled.

Full frontend suite once: **16 files / 88 tests passed** (77 baseline + 11 new), exit 0.

## 11. TypeScript / build

- `npx tsc --noEmit`: clean (exit 0). One compile error during development (`tasks` prop required) was fixed by making it optional — the component fetches its own task list when none passed.
- `npm run build`: success (✓ built). Pre-existing chunk-size warning only.

## 12. Migration status

**No migration needed** — no new tables or columns; subtasks reuse the existing `Task.parent_id`, estimates reuse `estimate_points`, capacity reuses `Sprint.capacity`. Alembic head remains `b2c3d4e5f6a7` (single head, unchanged).

## 13. Known pre-existing failures

Same 4 phase 38–40 route-pin failures documented in Phases 44–46 (environment artifacts around `app.routes` pin checks): `test_phase38_analytics.py::test_delivery_and_dora_registered_on_analytics_router`, `test_phase39_analytics_clients.py::test_project_github_route_registered_once`, `test_phase40_github_reliability.py::test_frontend_analytics_time_urls_exist_in_backend`, `test_phase40_github_reliability.py::test_github_analytics_route_registered_exactly_once`. Unrelated to Phase 47; not touched.

## 14. Remaining limitations

1. MockAIProvider's breakdown is generic (fixed "Subtask 1/2"); deterministic heuristics drive the rest. A real provider would produce richer suggestions through the same sanitized pipeline.
2. Applying requires a specific task (parent) — project-level breakdowns with no parent task are preview-only (UI explains this).
3. Apply does not copy the parent's sprint/milestone/assignee to new subtasks (created unassigned, TODO); users assign them explicitly — safest default for advisory AI.
4. The 4 pre-existing route-pin failures remain (out of scope).
5. Suggested breakdown is capped at 8 items and text lengths bounded; longer breakdowns would need a later phase.
