# Phase 21: DevOps, Deployment & Infrastructure Intelligence

## Overview
DevFlow includes a comprehensive infrastructure intelligence system designed to track, manage, and analyze deployments, environments, and infrastructure health across projects. This system is entirely organization-scoped and focuses on visibility and coordination rather than actual cluster management (it tracks rather than hosts).

## Architecture

### Models
- **Environment**: Represents a target deployment environment (DEVELOPMENT, STAGING, PRODUCTION, PREVIEW).
- **Deployment**: Represents a single deployment event to an environment, tied to a release or commit.
- **DeploymentApproval**: Represents manual or automated approval requirements before a deployment can proceed.
- **EnvironmentVariable**: Secure storage for environment-specific configuration and secrets.
- **ServiceHealth**: Tracks the health and response times of services within an environment.
- **DeploymentIncident**: Tracks issues or degradations caused by a failed or faulty deployment.

### API Endpoints
- `/api/v1/environments`: CRUD for environments and variables.
- `/api/v1/deployments`: CRUD for deployments, plus actions like `start`, `cancel`, `rollback`.
- `/api/v1/deployment-incidents`: Management of deployment-related incidents.
- `/api/v1/infrastructure/analytics`: Metrics for deployment frequency, success rates, and MTTR.

## Deployment Lifecycle & Mock Engine
The deployment engine runs locally and supports the following states:
`QUEUED` → `BUILDING` → `DEPLOYING` → `SUCCESS` or `FAILED`

Failure simulation is supported via API for testing resilience and incident generation.

## Rollback Behavior
Rollbacks are treated as **new** deployments of a previously known-good state. 
- The system identifies the last successful deployment.
- A new deployment is created, explicitly marked as a rollback.
- Historical deployment records are strictly preserved and never mutated destructively.
- Audit events are generated for traceability.

## Environment Variables & Security
- Secrets are encrypted at rest.
- The API never returns plaintext secrets; it returns a masked value (`********`).
- Environment variables integrate with RBAC to ensure only authorized users can view or modify them.

## RBAC Permissions
New permissions introduced:
- `environments.view`, `environments.manage`
- `deployments.view`, `deployments.create`, `deployments.manage`, `deployments.approve`, `deployments.rollback`
- `incidents.view`, `incidents.manage`
- `infrastructure.analytics`

## Local Testing
All infrastructure logic is designed to work locally with SQLite without external dependencies (no Redis/Celery required). The mock deployment engine operates synchronously or via lightweight background tasks for seamless development.
