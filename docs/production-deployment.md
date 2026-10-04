# Production Deployment Guide

## Overview
DevFlow is designed to be easily deployed to modern cloud infrastructure using Docker. It consists of a FastAPI backend, a React/Vite frontend, and a PostgreSQL database.

## Architecture
- **Backend:** Python 3.13, FastAPI, Uvicorn (Stateless)
- **Frontend:** React, Vite (Static assets served via Nginx or similar)
- **Database:** PostgreSQL (Stateful)
- **Scheduler:** Lightweight in-process scheduler (single worker recommended to avoid conflicts).

## Running with Docker Compose
The provided `docker-compose.yml` sets up the complete stack:
1. `docker-compose build`
2. `docker-compose up -d`

## Environment Configuration
See `docs/production-environment.md` for a complete reference on configuring environment variables.

## Migrations
Before starting the backend in a new environment, apply Alembic migrations:
```bash
docker-compose exec backend alembic upgrade head
```

## Scaling
- **Frontend:** Can be deployed to any static hosting provider (Vercel, Netlify, CloudFront, S3, Cloudflare Pages).
- **Backend:** Can be scaled horizontally behind a load balancer, but ensure `JOB_SCHEDULER_ENABLED=true` is set on **only one instance** or they will process jobs redundantly since the current Phase 23 scheduler is in-memory.
