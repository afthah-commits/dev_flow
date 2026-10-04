# Production Environment Guide

DevFlow uses environment variables for all configuration. Never commit secrets to the repository.

## Backend Variables
- `DATABASE_URL`: Connection string for PostgreSQL (e.g., `postgresql://user:pass@host:5432/db`)
- `SECRET_KEY`: A strong random string for JWT signing
- `JWT_ALGORITHM`: Usually `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration time for tokens (default 1440 = 24h)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed frontend origins for CORS (e.g., `https://devflow.example.com`)
- `JOB_SCHEDULER_ENABLED`: Set to `true` on a single instance to enable background jobs
- `AI_PROVIDER`: Choose `mock`, `openai`, `anthropic`, etc.
- `AI_API_KEY`: Secret key for AI provider
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`: OAuth app credentials

## Frontend Variables
Frontend variables are injected at build time. For Vite, they must be prefixed with `VITE_`.
- `VITE_API_URL`: The public URL of the backend API (e.g., `https://api.example.com/api/v1`)
- `VITE_WS_URL`: The public URL of the backend WebSocket (e.g., `wss://api.example.com/api/v1/ws`)

> **Note:** The frontend build command will bake these variables into the static assets. Ensure they don't contain backend secrets.
