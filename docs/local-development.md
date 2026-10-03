# Local Development Guide

This guide covers setting up DevFlow completely on your local machine.

## Prerequisites
- Python 3.10+
- Node.js 20+
- Git

## 1. Backend Setup

### Virtual Environment
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

### Dependencies
```bash
pip install -r requirements.txt
```

### Configuration
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
For local testing, the default mock AI provider requires no keys.
To use OpenAI, set `AI_PROVIDER=openai` and add your `AI_API_KEY`.

### Database Migration
Create the initial SQLite database and apply migrations:
```bash
alembic upgrade head
```

### Backend Startup
```bash
uvicorn app.main:app --reload
```
The API runs at `http://localhost:8000`. You can view the docs at `http://localhost:8000/docs`.

## 2. Frontend Setup

### Dependencies
```bash
cd frontend
npm install
```

### Configuration
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Default API URL is `http://localhost:8000/api/v1`.

### Frontend Startup
```bash
npm run dev
```
The app runs at `http://localhost:5173`.

## 3. Optional Configuration

### GitHub Setup
To test GitHub integration:
1. Go to your GitHub Developer Settings -> OAuth Apps.
2. Create a new app.
3. Homepage URL: `http://localhost:5173`
4. Authorization callback URL: `http://localhost:5173/settings/integrations/github/callback`
5. Copy the Client ID and Client Secret into the backend `.env`.
6. Generate a 32-byte encryption key for `GITHUB_TOKEN_ENCRYPTION_KEY`:
   `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### Mock AI Configuration
By default, the backend uses `AI_PROVIDER=mock`. This returns simulated tasks and conversations instantly, perfect for testing without API usage.

## 4. Testing

### Backend Tests
```bash
cd backend
python -m pytest
```

### Frontend Tests
```bash
cd frontend
npm test          # Run Vitest
npx tsc --noEmit  # Type check
npm run lint      # Linting
npm run build     # Production build test
```
