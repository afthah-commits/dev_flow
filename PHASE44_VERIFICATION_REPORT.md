# Phase 44 Verification Report — Project & Workspace Templates

**Status:** COMPLETE ✅
**Date:** 2026-10-06
**Commit:** `feat: add project workspace templates`

## 1. Template Architecture

New organization-scoped template system built on the existing stack (FastAPI +
SQLAlchemy + Alembic backend, React + Vitest frontend). Two new tables only:

- `project_templates` — id, organization_id (FK CASCADE), name, description,
  `is_archived` flag, created_by_id, timestamps.
- `project_template_tasks` — id, template_id (FK CASCADE), position, title,
  description, priority (reuses `TaskPriority`), `label_names` (JSON list of
  label *names*), `checklist_items` (JSON list of strings).

Models: [backend/app/models/project_template.py](backend/app/models/project_template.py)
Schemas: [backend/app/schemas/template.py](backend/app/schemas/template.py) (existing `TaskTemplate*` schemas untouched)
Routes: `/api/v1/templates/project*` in [backend/app/api/v1/templates.py](backend/app/api/v1/templates.py) — new sub-router; the pre-existing task-template endpoints were moved under `/templates/task*` to keep every route unique (contract test `test_no_duplicate_routes_anywhere_in_app` passes).

No concrete project/task IDs are stored in templates — only relative content.
No polymorphic infrastructure. No new PM concepts: templates only reference
existing Labels (by name) and produce existing Tasks with existing Checklists.

## 2. Supported Template Content

- Ordered template tasks (position, title, description, priority)
- Checklist items per template task
- Label names per template task (resolved against org labels at apply time;
  unknown names are skipped, not fatal)
- Template metadata (name, description, archived state)

Sprints/milestones are deliberately NOT modeled: they are project-scoped rows
and there is no safe relative representation in this schema; template tasks
therefore cannot reference them (documented limitation).

## 3. CRUD Behavior

| Endpoint | Method | Notes |
|---|---|---|
| `/templates/project` | POST | Create with nested tasks; whitespace/empty names → 422 |
| `/templates/project` | GET | Org-scoped list; `include_archived=true` to include archived |
| `/templates/project/{id}` | GET | 404 unless owned by the org |
| `/templates/project/{id}` | PATCH | Update fields and/or atomically replace the task list |
| `/templates/project/{id}/archive` | POST | Soft-archive; archived templates hidden by default |
| `/templates/project/{id}` | DELETE | Hard delete (safe: projects are independent copies) |
| `/templates/project/{id}/create-project` | POST | Create a project from the template |

## 4. Create Project from Template

`POST /templates/project/{id}/create-project` with `{name, description?}`:

1. Validates org membership; project creation restricted to OWNER/ADMIN
   (matches the project-creation permission tier).
2. Rejects archived templates (400) and foreign templates (404).
3. Generates a unique slug (same algorithm as `POST /projects`).
4. Creates the project, then copies every template task as a normal `Task`
   (with `task_key`, `position`, `priority`), bulk-precomputing globally
   unique `task_key`s to avoid the global UNIQUE index collision.
5. Copies checklist items as real `ChecklistItem`s and links org `Label`s by
   name through `task_labels`.
6. Everything runs in one transaction: any failure → `db.rollback()` → no
   half-created project. Verified by a dedicated rollback test.
7. The template is never modified; each project receives fully independent
   copies (no FK/reference back to template rows).

## 5. Data Independence Guarantees (tested)

- Editing a template does NOT modify projects already created from it.
- Deleting a template does NOT delete/alter generated projects or tasks.
- Modifying a generated project does not affect the template.
- Duplicate creation from the same template works (unique slugs, unique keys,
  independent task copies).
- Template tasks have no `project_id`/`task_id` columns (schema-level pin).

## 6. Security Verification

- Unauthenticated → 401 (GET and POST).
- Missing org header → 400/403.
- Non-member with foreign `X-Organization-Id` → 403 (list + create).
- Foreign template id → 404 on get/patch/delete/create-project (cross-tenant
  leakage test: no task rows created).
- Member role may read templates but cannot create projects from them (403).
- All checks are server-side via `require_organization_member` + org-scoped
  queries; frontend filtering is cosmetic only.

## 7. Performance

- Task list for one template is loaded once and iterated in memory (no N+1).
- `task_key` uniqueness is resolved with one bulk `IN` query, not per-task
  probes.
- Label lookup is one bulk query for all referenced names.
- No caching introduced. Template creation with N tasks is 1 INSERT batch.

## 8. Migration Verification

- New revision `a1b2c3d4e5f6_phase44_project_templates.py` on top of head
  `86f704f37613`; no existing migration modified.
- Cycle executed on a fresh SQLite DB:
  `upgrade head` → `downgrade -1` → `upgrade head` → `alembic current` shows
  `a1b2c3d4e5f6 (head)`. Downgrade drops both tables + indexes cleanly.

## 9. Backend Tests

`backend/tests/test_phase44_templates.py` — 18 focused tests:
auth (401), org header, non-member 403, foreign-template isolation, CRUD
roundtrip, validation (empty/long names, unknown id), archive + list filter,
apply (tasks/checklists/labels), unknown-label tolerance, independence in all
directions, duplicate creation, archived-template rejection, no-ID-leak schema
pin, member-role RBAC, cross-tenant leakage, transaction rollback + retry,
blank project creation.

**Full backend suite:** `python -m pytest tests -q` → **267 passed / 4 failed**
The 4 failures (`test_phase38/39/40` route-registration pins) are **pre-existing
on a clean checkout** (verified via `git stash` + re-run) — an environment
artefact in how `app.routes` enumerates nested routers; unrelated to Phase 44
(no route duplication: `test_no_duplicate_routes_anywhere_in_app` passes).

## 10. Frontend Tests

`frontend/src/pages/Templates.test.tsx` — 11 tests: list, loading, empty,
error, create, edit, archive, delete, preview + create-project-from-template,
blank project creation preserved, template creation via ProjectForm.

**Full frontend suite:** `npx vitest run` → **14 files / 67 tests passed**
(includes the 11 new Phase 44 tests).

## 11. TypeScript / Build

- `npx tsc --noEmit` → clean (0 errors).
- `npm run build` → success (chunk-size warning is pre-existing).

## 12. Commit

Single commit on top of `65fcbd0`: `feat: add project workspace templates`.

## 13. Remaining Limitations

1. Sprints/milestones are not part of template content (no safe relative
   representation; documented in §2).
2. Template labels are matched by name; labels that don't exist in the org are
   skipped rather than auto-created (avoids surprise side effects).
3. Template task assignment (assignee), due dates and estimates are not part
   of template content.
4. No template versioning/usage counters.
5. 4 pre-existing route-pin test failures in phases 38–40 reproduce on a clean
   checkout and are out of Phase 44 scope.
