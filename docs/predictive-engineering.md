# Predictive Planning & Engineering Intelligence

## Overview
Phase 26 transforms DevFlow from an AI assistant into a deep engineering planning platform. It adds deterministic mathematical forecasting and risk scoring to supplement the AI text recommendations.

## Features Added
1. **Forecast Engine**: `/api/v1/ai/projects/{project_id}/forecast` evaluates remaining task burden against recent sprint velocity to predict completion.
2. **Risk Engine**: `/api/v1/ai/projects/{project_id}/risk-engine` assigns an overall risk score from 0-100 by calculating overdue tasks, blocked items, and infrastructure problems.
3. **Smart Sprint Planner**: `/api/v1/ai/projects/{project_id}/sprint-planning` measures total member capacity and fits backlog items using Priority to prevent over-allocation.
4. **Task Priorities Engine**: Deterministically scores backlog tasks for impact and urgency.
5. **AI Project Health Report**: Uses `MockAIProvider` to synthesize recent GitHub, DevOps, and Issue data into a summary.

## Architecture
Calculations are located in `backend/app/services/predictive_intelligence.py`. 
AI routes in `backend/app/api/v1/ai.py` handle the HTTP transport, fetching necessary RBAC-constrained context and calling the deterministic functions.

## Testing & Security
- Isolated via `organization_id` on all API endpoints.
- Tests written in `backend/tests/test_predictive_planning.py` verify accuracy and cross-tenant rejections.
