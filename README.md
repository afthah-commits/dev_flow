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
├── backend/            # FastAPI backend
│   ├── alembic/        # Database migrations
│   ├── app/            # Application code
│   │   ├── api/        # REST endpoints
│   │   ├── models/     # SQLAlchemy models
│   │   ├── schemas/    # Pydantic schemas
│   │   ├── services/   # Business logic (AI, GitHub, Analytics)
│   ├── tests/          # Pytest suite
├── frontend/           # React frontend
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/      # Route pages
│   │   ├── lib/        # API clients
│   │   ├── types/      # TypeScript definitions
├── docs/               # Technical documentation
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
