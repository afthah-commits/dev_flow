# AI Engineering Intelligence Platform

## Overview
Phase 25 upgrades DevFlow's AI capabilities into a comprehensive Engineering Intelligence Platform. The AI now serves as an advisory system, helping project managers and developers understand project health, identify risks, plan sprints, and analyze deployments—all without bypassing human oversight or data boundaries.

## Architecture

- **AI Context Engine**: Resides in `backend/app/services/ai_context.py`. Aggregates bounded contextual data (tasks, sprints, GitHub activity, deployments) using SQL aggregations to prevent N+1 queries.
- **AI Models**: Introduced `AIProjectMemory` and `AIUsage` in `backend/app/models/` for long-term project-level AI awareness and cost tracking.
- **Intelligence Endpoints**: 
  - `/ai/projects/{id}/summary`
  - `/ai/projects/{id}/risks`
  - `/ai/projects/{id}/prioritize`
  - `/ai/projects/{id}/sprint-plan`
  - `/ai/projects/{id}/github/summary`
  - `/ai/releases/{id}/analysis`
  - `/ai/projects/{id}/deployment-analysis`
  - `/ai/projects/{id}/daily-brief`

## Security and Compliance
- AI never directly executes mutations without explicit human confirmation.
- The `ai_context` engine verifies `current_user` permissions, `organization_id`, and existing RBAC on *every* request before aggregating data.
- API limits constrain retrieved data (e.g. max 10 recent PRs) to avoid context bloat and out-of-memory errors.
- External secrets and sensitive credentials are mathematically isolated and never fed into prompts.

## AI Command Center
The frontend features a new `/ai` endpoint serving as a command center to quickly poll Project Status, Daily Briefs, and Identified Risks.
