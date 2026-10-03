# Task Management Architecture (Phase 3)

## Overview
Phase 3 introduced a fully functional task tracking and Kanban system integrated natively into DevFlow. It bridges the gap between project organization and day-to-day execution.

## Domain Model
- **Task**: Represents a discrete unit of work within a project.
- **Fields**:
  - `id` (UUID): Primary key.
  - `project_id` (UUID): Foreign key associating the task to exactly one project (cascade delete enabled).
  - `creator_id` (UUID): Foreign key denoting who made the task.
  - `assignee_id` (UUID): Optional foreign key to support task assignment.
  - `title`, `description`, `due_date`: Core properties.
  - `labels`: JSON array to support dynamic multi-label tagging.
  - `status`: Enum (TODO, IN_PROGRESS, IN_REVIEW, DONE).
  - `priority`: Enum (LOW, MEDIUM, HIGH, CRITICAL).
  - Timestamps: `created_at`, `updated_at`.

## Architecture & Security
- **Strict Project Scoping**: A task does not possess an `owner_id`. Instead, security checks resolve the `project_id` and explicitly verify if the current authenticated user owns that project. A failure returns a standard `404 Not Found` for safety.
- **Drag & Drop**: Driven via HTML5 Native Drag & Drop API in React (`onDragStart`, `onDrop`) to prevent adding unnecessarily heavy dependencies (like `react-beautiful-dnd`). 
- **Optimistic UI Updates**: State is mutated locally in React during drops and instantly rolled back if the backend HTTP PATCH fails. 

## Frontend Flow
- Users navigate to a Project Details page, which splits the view between a high-level summary header (with total task stats) and a workspace container.
- The workspace toggles between a Kanban view (for execution tracking) and a List view (for tabular data overview). 
- Modals invoke `TaskForm` reusing state across Creation and Updates to ensure dry component architecture.
