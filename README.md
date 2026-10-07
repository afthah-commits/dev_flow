# DevFlow

DevFlow is a complete AI-assisted developer workspace. It combines project management, kanban boards, GitHub integration, analytics, and an integrated AI assistant into a single, cohesive application.

## Features
- **Project Management**: Create and track multiple projects.
- **Kanban Task Board**: Manage tasks with drag-and-drop statuses.
- **GitHub Integration**: Connect repositories to view recent commits, PRs, and issues directly inside your workspace.
- **AI Developer Assistant**: Context-aware AI chat that can understand your project, analyze code context, and generate actionable tasks.
- **Analytics**: Deep insights into task completion trends, project health, deadlines, and activity metrics.
- **Notifications**: In-app deduplicated notifications for overdue tasks, project health risks, and more.

## Tech Stack
- **Backend**: Python 3, FastAPI, SQLAlchemy, SQLite (Development), Alembic
- **Frontend**: Node.js, React, Vite, Tailwind CSS v4, TypeScript, Recharts
- **Architecture**: Separated frontend SPA + backend REST API.

## Project Structure
```
devflow/
â”œâ”€â”€ backend/            # FastAPI backend
â”‚   â”œâ”€â”€ alembic/        # Database migrations
â”‚   â”œâ”€â”€ app/            # Application code
â”‚   â”‚   â”œâ”€â”€ api/        # REST endpoints
â”‚   â”‚   â”œâ”€â”€ models/     # SQLAlchemy models
â”‚   â”‚   â”œâ”€â”€ schemas/    # Pydantic schemas
â”‚   â”‚   â”œâ”€â”€ services/   # Business logic (AI, GitHub, Analytics)
â”‚   â”œâ”€â”€ tests/          # Pytest suite
â”œâ”€â”€ frontend/           # React frontend
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ components/ # React components
â”‚   â”‚   â”œâ”€â”€ pages/      # Route pages
â”‚   â”‚   â”œâ”€â”€ lib/        # API clients
â”‚   â”‚   â”œâ”€â”€ types/      # TypeScript definitions
â”œâ”€â”€ docs/               # Technical documentation
```

## Local Setup

Please see [docs/local-development.md](docs/local-development.md) for complete setup instructions.

### Quick Start
1. **Backend**:
```bash
cd backend
python -m venv venv
# activate venv
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```
2. **Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## AI Setup
DevFlow supports real AI providers (OpenAI) and a Mock provider for local testing. Configure the backend `.env` to switch between them.

## GitHub Integration
Register a GitHub OAuth Application and configure the keys in the backend `.env` file to enable repository linking.

## Testing
- **Backend**: Run `pytest` inside the `backend/` directory.
- **Frontend**: Run `npm run test`, `npm run lint`, and `npx tsc --noEmit` in `frontend/`.

## Troubleshooting
- **Database issues**: Ensure `alembic upgrade head` ran successfully.
- **CORS issues**: Ensure frontend matches the origins in backend settings.


## Phase 18: Advanced Reporting + Custom Dashboards
Phase 18 adds advanced, fully-customizable dashboards, reporting engines, data exports, and metric aggregations, protected under DevFlow's organization-scoped tenant models and custom roles.


## Phase 19: Enterprise Governance + Compliance
Phase 19 introduces the foundational structures necessary for SOC2 readiness encompassing organizational data retention policies, explicit audit triggers, domain validation mocks, scoped security policies, and robust multi-tenant environment configurations.


## Phase 20: Enterprise Integration Hub
Provides comprehensive external application boundaries securely integrating deterministic Slack, Google Calendar, and Email mock components alongside advanced webhook tracking and usage analytics pipelines.

## Phase 21: DevOps, Deployment & Infrastructure Intelligence
Phase 21 transforms DevFlow into a production-oriented deployment workspace, tracking environments, deployment histories, mock health metrics, release rollbacks, and incident generation under the existing tenant boundaries.

## Phase 30: Visual Workflow Studio & Advanced Form Builder
Phase 30 upgrades the structured Workflow Builder into a professional visual Workflow Studio at `/workflows/:workflowId/studio`: an infinite canvas (pan/zoom/grid, drag-and-drop states, visual transition links, minimap), a right-side configuration panel for states, transitions, safe conditions, ordered actions, and approval rules, plus workflow validation (PASS/WARNING/ERROR publish gate), a dry-run simulator, immutable DRAFT/PUBLISHED/ARCHIVED versioning, execution history with step-through previews, an advanced drag-and-drop form builder with conditional fields, realtime workflow events, and an advisory AI design assistant that can only produce drafts for explicit human review. See [docs/visual-workflow-studio.md](docs/visual-workflow-studio.md).

## Final Release Status (Phase 50)

DevFlow is feature-complete for this roadmap. Final verification status:

- **Backend**: FastAPI + SQLAlchemy + Alembic (single head `b2c3d4e5f6a7`; fresh databases migrate cleanly). Full pytest suite passes with 0 failures.
- **Frontend**: React + Vite + TypeScript; vitest suite, `tsc --noEmit`, and production build all pass.
- **Security model**: JWT auth, organization-scoped multi-tenancy with server-side RBAC (incl. custom roles), user-scoped dashboard layouts, org-scoped search/knowledge, restricted client portal, API keys, and audit logging of sensitive operations.
- **AI safety model**: the AI layer is advisory-only and deterministic under `MockAIProvider`. AI output is untrusted input, strictly sanitized and bounded (max 3 breakdown levels, 8 suggestions per level, 32 nodes), never mutates data by itself, and every apply flow re-validates permissions server-side inside one transaction.
- **Production configuration**: copy `.env.example` and set a strong `SECRET_KEY` (the app warns loudly if the development default is used), `DATABASE_URL`, `FRONTEND_URL`/`ALLOWED_ORIGINS`, and provider keys. See [docs/production-environment.md](docs/production-environment.md) and [docs/production-deployment.md](docs/production-deployment.md).

Run `python -m pytest tests -q` in `backend/` and `npm run test && npx tsc --noEmit && npm run build` in `frontend/` to reproduce the final verification. See [PHASE50_FINAL_VERIFICATION_REPORT.md](PHASE50_FINAL_VERIFICATION_REPORT.md) for the complete final report.
