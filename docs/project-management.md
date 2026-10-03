# Project Management Architecture (Phase 2)

## Overview
Phase 2 introduced the core Project Management capabilities to DevFlow, transforming the basic authentication shell into a functioning developer workspace.

## Domain Model
- **Project**: Represents a developer's software project.
- **Fields**: 
  - `id` (UUID): Primary key.
  - `owner_id` (UUID): Foreign key mapping to `users.id`.
  - `name`, `slug`, `description`: Core metadata.
  - `status`: Enum (Planning, Active, On Hold, Completed, Archived).
  - `priority`: Enum (Low, Medium, High, Critical).
  - `tech_stack`: JSON array of strings representing technologies.
  - `start_date`, `end_date`: Optional project timelines.
  - Timestamps: `created_at`, `updated_at`.

## Security & Access Control
- **Strict Tenant Isolation**: All `Project` queries are rigidly filtered by `owner_id == current_user.id`. 
- Users attempting to fetch, update, or delete a project they do not own will receive a `404 Not Found` to prevent exposing the existence of other users' projects (as opposed to a 403).

## API Architecture
The project API follows a standard RESTful convention under `/api/v1/projects`:
- `GET /` - Paginated list of projects with filtering (search, status, priority) and sorting.
- `POST /` - Creates a new project and automatically assigns the current authenticated user as the owner.
- `GET /{id}` - Fetches detailed project information.
- `PATCH /{id}` - Applies partial updates to project fields.
- `DELETE /{id}` - Removes the project.

## Frontend Implementation
- **Dashboard**: High-level overview of metrics (Active, Completed) and recently updated projects.
- **Project Directory**: Fully integrated with the backend API for real-time searching and filtering of the project portfolio. Debounced inputs prevent excessive API requests.
- **Forms**: Reusable project creation and editing components leveraging Tailwind CSS for a premium dark-mode interface.
