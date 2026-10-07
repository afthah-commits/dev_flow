# Phase 49 Verification Report — AI Breakdown Editor & Route Contract Hardening

## 1. AI editor implementation

The Phase 48 progressive breakdown gained a lightweight review/edit layer in the existing [ProjectAIPlanning.tsx](frontend/src/components/ProjectAIPlanning.tsx) — no new page, no UI redesign. After Analyze, the suggestion tree becomes an editable **draft** (local preview state; nothing persisted until Apply Selected). Each node shows title, description (root level), priority, estimated points, selection checkbox, and per-node actions: Edit (✎), Add child (＋), Delete (✕), Move under… (dropdown of valid targets). The tree header shows total selected effort, selected/total node count and tree depth (x/3). Phase 47/48 features (analyze, loading, estimate+confidence, complexity, capacity, risks, expand/collapse, cascade selection, Apply Selected, Cancel, error/success states) are all preserved.

## 2. Tree editing behavior

- **Edit**: inline form (title/description/priority/estimated points) with Save and Cancel; cancel reverts.
- **Add child**: appends a pre-selected "New sub-suggestion"; blocked with a clear error at max depth (3 levels), >8 children per node, or >32 total nodes.
- **Delete**: removes the node **and its subtree**; a `confirm()` is required when children exist (never silently orphans); cancel keeps the node. Deleting = simply not sending the node on Apply (covered by a dedicated test).
- **Move**: "Move under…" dropdown of valid targets — excludes the mover itself and its descendants (cycle prevention), enforces depth ≤3 and ≤8 children after the move. Node identity is preserved via a structural copy (same node objects, fresh arrays), so selection survives the move and keys re-map correctly.
- **Selection** keeps Phase 48 semantics (deselect parent cascades to descendants).

## 3. Validation

Client-side warnings (`editor-warnings` panel): empty titles, >200-char titles, >8 children, points out of 0–100, depth >3, node count >32, duplicate suggestion ids. The frontend is NOT trusted: the server re-validates everything on Apply. Phase 49 hardened server validation in [ai.py](backend/app/api/v1/ai.py) `_validate_suggestion_tree`: overlong titles/descriptions are now **rejected (422)** rather than silently truncated, and invalid `estimated_points` (non-numeric, boolean, negative, >100) are **rejected** — booleans are rejected at the schema level with a `mode="before"` validator because pydantic lax mode otherwise coerces `True → 1.0`. Applied per-suggestion points now actually persist to `Task.estimate_points` (this was silently dropped in Phase 48 — fixed).

## 4. Apply safety

Unchanged guarantees, verified for edited trees: auth + org membership + project/task ownership re-checked; complete tree validated before any write (depth, count, parent integrity, lengths, priority normalization, points); only selected nodes created; hierarchy preserved via `parent_id` with parent flush before children; single `db.commit()` with full rollback; audit event `ai.planning_applied` includes created count/keys/depth. Malformed payloads produce clean 422 JSON responses (see §6 fix).

## 5. Security

401 unauthenticated / 403 non-member verified for edited-tree applies; cross-tenant suggestions impossible (foreign project/task ids → 403/404, nothing created); AI/user-edited output treated as untrusted — strict plain-data key set unchanged from Phase 48 (`title/description/priority/suggestion_id/estimated_points/level/parent_suggestion_id/children`), no executable configuration; prompt-injection tests from Phases 47–48 still pass unchanged.

## 6. Route inventory hardening

- [conftest.py](backend/tests/conftest.py) `iter_flattened_routes()` is the single authoritative helper: yields concrete routes (descending into nested `_IncludedRouter` wrappers) exposing effective `path` (include prefix + child path), `methods`, `name` and `endpoint`; works on flat (older FastAPI) and nested (0.142) registration. No production routing was modified.
- [test_phase49_breakdown_editor.py](backend/tests/test_phase49_breakdown_editor.py) adds hardening pins: helper self-test (paths/methods/endpoint present), nested prefix resolution (analytics, dashboard, nested project/task resources), exactly-once registration for analytics (delivery/dora/github), AI planning (analyze/apply), dashboard (layout/stats) and search routes (per method+path combination), duplicate effective method+path detection, and a frontend-contract check that the frontend's planning API calls map to registered backend routes. All existing Phase 38–40 route tests remain and pass.
- **Pre-existing production bug found & fixed** ([exceptions.py](backend/app/core/exceptions.py)): the `RequestValidationError` handler embedded raw pydantic v2 error entries — whose `ctx` carries a non-JSON-serializable `ValueError` — into `JSONResponse`, crashing the 422 response itself. Now normalized via `jsonable_encoder`. Surfaced by the new schema validator; fixed in the handler, not by avoiding the validation.

## 7. Backend focused tests

[test_phase49_breakdown_editor.py](backend/tests/test_phase49_breakdown_editor.py): **16 passed** — edited tree fully accepted (titles/description/priority/points persisted, user-added child, reparented node), overlong text 422, invalid points 422 (incl. booleans), empty title 422, cycle/self-parent/unknown-parent 422, depth/count 422, deleted-node semantics, permissions (401/403/404) with nothing created cross-tenant, audit with correct counts, route helper self-test, prefix resolution, exactly-once pins, duplicate detection, frontend contract. Plus Phase 47/48 files re-run: 31 passed (back-compat).

## 8. Backend full suite

`python -m pytest tests -q`: **337 passed, 0 failed** (exit 0) — target met (321 baseline + 16 new).

## 9. Frontend tests

Focused [ProjectAIPlanning.test.tsx](frontend/src/components/ProjectAIPlanning.test.tsx): **19 passed** — 11 from Phase 47/48 (all preserved) + 8 new: edit mode/save/cancel (local revert verified), add child with depth-limit error, delete with confirm (subtree gone, siblings re-keyed), delete-cancel keeps node, move with cycle prevention + selection preservation, validation warnings for empty title, node count/depth stats, server 422 detail surfaced in error state.

Full frontend suite: **16 files / 96 tests passed** (exit 0).

## 10. TypeScript

`npx tsc --noEmit`: clean (exit 0).

## 11. Build

`npm run build`: success (✓ built in 6.2s). Pre-existing chunk-size warning only.

## 12. Migration status

No migration — preview-only editing, existing `Task` model reused (including `estimate_points`, which now actually receives per-suggestion values). Single Alembic head unchanged (`b2c3d4e5f6a7`).

## 13. Performance

Edits are purely local state (zero API calls while editing); Apply sends one request; ≤32 nodes bounds all validation work; apply remains one transaction with per-parent flush only where children need the PK; no polling, workers, or external AI.

## 14. Remaining limitations

1. "Move" exposes a dropdown of valid targets rather than drag-and-drop (deliberate scope control).
2. Deleting a parent always deletes its subtree (with confirm); per-child adoption/re-attachment is manual via Move before Delete.
3. Selection keys are index-path based; after structural edits keys re-map via identity/suggestion_id where possible — bulk re-keying of deeply nested custom selections could theoretically surprise, though covered by tests.
4. The `RequestValidationError` handler fix changes 422 response bodies to jsonable-encoded errors (previously the handler crashed on custom-validator errors — no stable prior format existed to break).
5. Route pins are robust to nested/flat registration but a future FastAPI release renaming `_IncludedRouter` internals would require updating the helper (single place, tested).
6. Pre-existing chunk-size build warning remains (cosmetic).
