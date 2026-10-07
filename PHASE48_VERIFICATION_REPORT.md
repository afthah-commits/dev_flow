# Phase 48 Verification Report — Regression Cleanup & Progressive AI Breakdown

## 1. Route-pin root causes

The 4 long-standing failures were **not** application bugs — the routes were registered and reachable. Root cause: the venv's FastAPI was upgraded to **0.142.2**, which stopped flattening `include_router(...)` calls into `app.routes`. Since FastAPI ≥0.135, each include adds a single lazy `_IncludedRouter` wrapper object; the real `APIRoute` objects live *inside* the wrapper (with the include prefix held in `include_context`), and the wrappers expose no `path`/`methods` themselves.

The Phase 38–40 pin tests iterate `app.routes` and read `getattr(r, "path", "")` / `hasattr(r, "methods")`:
- On the old FastAPI, `app.routes` was flat → tests passed.
- On 0.142, every business route became a pathless wrapper → `{getattr(r,"path","")}` collapsed to essentially `""` (plus the few framework routes), so `/api/v1/analytics/delivery`, `/api/v1/analytics/dora` and the github route were "not found", duplicate detection became trivially "clean", and the frontend-contract test found "no" backend routes. The tests failed from the moment the FastAPI dependency was upgraded — an environment/version artifact, not a route-registration defect.

Reproduced independently (all 4 failing) before touching anything, and verified via a manual flatten that `/api/v1/analytics/delivery`, `/api/v1/analytics/dora`, `/api/v1/analytics/projects/{project_id}/github`, all team-workload/productivity routes etc. were present, single-registered, with the right HTTP methods.

## 2. Route fixes

No application code changed. The fix preserves the tests' original assertions 1:1:

- [conftest.py](backend/tests/conftest.py) now provides `iter_flattened_routes()` — yields every concrete route, descending into `_IncludedRouter` wrappers, and exposes `path = include_prefix + child.path` (the effective request path), `methods`, `name`, `endpoint` via a lightweight `_FlattenedRoute` proxy. Written to work on both flat (older FastAPI) and nested (newer) registration.
- The 5 affected assertions (4 failing tests + the neighbouring `test_no_duplicate_routes_anywhere_in_app`) now iterate `iter_flattened_routes()` instead of `app.routes`. **Every original assertion is unchanged** — same expected paths, same "exactly once" checks, same duplicate detection, same frontend-contract matching.

Verified: `/api/v1/analytics/delivery` and `/api/v1/analytics/dora` → GET registered exactly once; project github analytics → GET registered exactly once; no duplicate effective (path, methods) pairs anywhere; all Phase 38 analytics tests (31) pass.

## 3. Progressive AI breakdown

Phase 47's flat breakdown remains fully supported; suggestions now may carry safe progressive fields: `suggestion_id`, `estimated_points`, `level`, `parent_suggestion_id`, `children`. `MockAIProvider` returns a deterministic 2-level example tree (Backend payment integration → provider configuration / payment service / error handling; Frontend checkout → UI / state handling; plus webhook handling & testing) when the nested schema is requested — theамины existing `subtasks` contract property is reused, no new AI architecture.

Sanitizer ([planning.py](backend/app/services/ai/planning.py) `sanitize_suggestions`) now normalizes trees: malformed nodes dropped, non-string titles rejected, non-string priorities coerced to MEDIUM, per-suggestion points clamped to 0–100, strings truncated, and unknown/duplicate/cyclic ids dropped. UI ([ProjectAIPlanning.tsx](frontend/src/components/ProjectAIPlanning.tsx)): expand/collapse per node, indented hierarchy, per-suggestion point badges, select/unselect with **deselect-parent-cascades-to-children**, total selected effort, max-depth warning. All Phase 47 UI features (analyze button, loading, estimate, confidence, risks, capacity, apply selected, cancel, error state) remain.

## 4. Hierarchy limits

- Max depth **3 levels** (root level 0 → level 2); deeper nodes dropped on sanitize and rejected (422) on apply.
- Max **8** suggestions per parent / per level (provider output truncated; apply rejects >8 in `_validate_suggestion_tree`).
- Max **32** total suggested nodes (`MAX_TOTAL_NODES`); apply enforces `MAX_APPLY_TOTAL_NODES = 32` server-side.

## 5. Apply transaction behavior

`POST /planning/apply` now validates the **complete tree server-side before any write** (`_validate_suggestion_tree`): unknown `parent_suggestion_id` → 422; self/circular links → 422; duplicate ids → 422; depth/count violations → 422; invalid priorities coerced to MEDIUM; points clamped. Only selected nodes are created (client sends the selected subtree), parent-child relationships preserved via `task.parent_id` (child recursion flushed the parent first within the same transaction — found and fixed a real bug where children got `parent_id=NULL` because the in-constructor PK default wasn't yet assigned). One `db.commit()`, full rollback on failure (verified by a failing-commit test: nothing persisted). Permissions re-checked server-side; audit event records created count/task keys and actual tree depth.

## 6. Security

Unchanged guarantees, re-verified: 401 unauthenticated; org membership enforced; foreign project/task → 403/404; suggestions strictly plain-data (`title/description/priority/suggestion_id/estimated_points/level/parent_suggestion_id/children` only — no executable configuration, verified by key-set walk in the injection test); untrusted task text bounded (500 chars) with the same system-prompt injection guard; AI never bypasses RBAC (same deps as every endpoint); rate limit applied to analyze. Cross-tenant apply/analyze attempts create nothing.

## 7. Performance

Bounded tree (32 nodes/3 levels) — no unbounded recursion; apply uses a recursive insert with flush-per-parent (necessary because children reference the parent PK), single commit; no background workers, polling, or external AI. Sanitizer is pure in-memory.

## 8. Backend focused tests

[test_phase48_progressive_breakdown.py](backend/tests/test_phase48_progressive_breakdown.py): **18 passed** — route inventory (effective paths, exactly-once, no duplicates, GET methods), flat compatibility, nested sanitize + parent links, max depth (provider output truncation + apply 422), max nodes (8/parent apply 422), total-32 cap, unknown/circular parent 422, invalid priority coercion with hierarchy preserved, invalid AI output normalization, preview non-mutation, apply only-selected preserving hierarchy, commit-failure rollback, permissions/org isolation, injection safety, audit (incl. depth in metadata).

## 9. Backend full suite

`python -m pytest tests -q`: **321 passed, 0 failed** (exit 0). Target achieved — the 4 historical route-pin failures are fixed at the root (test harness updated for FastAPI 0.142 nested registration; all assertions preserved).

## 10. Frontend tests

Focused [ProjectAIPlanning.test.tsx](frontend/src/components/ProjectAIPlanning.test.tsx): **11 passed** — hierarchy rendering with depth attributes, expand/collapse, parent-child cascade selection, total effort updates, apply sends only selected subtree preserving hierarchy, apply disabled when none selected/cancel without mutation, error state, capacity insufficient-data, project-level apply disabled, max-depth warning.

Full frontend suite: **16 files / 88 tests passed** (exit 0).

## 11. TypeScript

`npx tsc --noEmit`: clean (exit 0).

## 12. Build

`npm run build`: success (✓ built in 7.4s). Pre-existing chunk-size warning only.

## 13. Migration status

**No migration needed** — no schema change (existing `Task.parent_id` supports the hierarchy). Single Alembic head unchanged (`b2c3d4e5f6a7`).

## 14. Remaining limitations

1. MockAIProvider's nested tree is a fixed 2-level deterministic example; depth-3 comes from the safe schema but richer real-provider output flows through the same sanitizer.
2. Apply flushes the parent before creating children (required to obtain the PK); with ≤32 nodes this remains a single transaction with no correctness risk.
3. Rollback verification uses a standalone in-memory session because the conftest nested-transaction fixture cannot survive a mid-transaction rollback (fixture limitation, documented).
4. The frontend contract scan (Phase 40 test) now sees flattened effective routes; future FastAPI upgrades that change internal routing wrappers may need the `iter_flattened_routes` helper extended similarly.
5. The 4 former route-pin failures are fixed for the current FastAPI version; hidden wrapper-detail changes in future FastAPI releases would need re-verification (assertions themselves unchanged).
6. Pre-existing chunk-size build warning remains (cosmetic, out of scope).
