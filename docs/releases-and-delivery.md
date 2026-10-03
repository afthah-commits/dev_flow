# Releases and Delivery (Phase 13)

DevFlow provides a comprehensive internal software delivery lifecycle simulation for engineering teams without requiring external cloud deployment hooks.

## Release Architecture
Releases form the central hub of software versions. They tie together `Task` and `ReleasePullRequest` items via junction tables.
- **Statuses**: `DRAFT` -> `PLANNED` -> `READY` -> `RELEASED` or `CANCELLED`.
- **Readiness Score**: Evaluates task completion, pipeline health, blocked tasks, and active deployments to produce a deterministic 1-100 release readiness score.

## Deployments and Environments
Deployments are mapped to specific `Environment` configurations (e.g. Staging, Production). 
Because DevFlow operates locally, the deployment engine is a deterministic Mock Simulator that executes state transitions (`QUEUED` -> `SUCCESS`) without external provisioning.
Rollbacks are fully supported by creating a new deployment linking to the `previous_deployment_id` with a `ROLLED_BACK` status on the original run.

## Pipelines
CI/CD runs are mocked through `PipelineRun` schemas. These provide a foundation for displaying commit-level workflows to developers within the DevFlow dashboard.

## Analytics
DevFlow now features robust Delivery Analytics natively tracking:
- Release Cycle Times
- Deployment Frequency
- DORA-style metrics (Change Failure Rate, Mean Time to Recovery).

## AI Release Notes
The AI integration builds comprehensive markdown notes. By scanning all completed tasks and merged pull requests linked to a specific `release_id`, the system will generate Draft Notes categorized into Features, Bug Fixes, and Improvements.

## RBAC
Only authorized Members or Admins with explicit Project Access (via `X-Organization-Id` and `require_organization_member` dependency checks) may trigger deployments, pipelines, or adjust environments.
