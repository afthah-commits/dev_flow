# Production Release Platform (Phase 32)

## Overview
The DevFlow Release Platform brings strict controls to local deployments. It provides a formal state machine to ensure code changes satisfy a suite of deterministic checks before they are permitted to reach mock production environments.

## State Machine Workflow
- **DRAFT**: Initial creation state.
- **PLANNED**: Development is active.
- **READY**: Automatic evaluation has determined a score of `> 80` (all tasks complete, notes written, env mapped, active workflows done).
- **APPROVED**: An explicit approval has been granted via RBAC `manage_releases` permission.
- **DEPLOYING**: In transit via mock environment.
- **DEPLOYED**: Successfully deployed.
- **ROLLED_BACK**: Rolled back successfully.
- **FAILED**: Deployment encountered an issue.

## Deterministic Readiness
Readiness is computed via `ReleaseEngine.evaluate_readiness`. It is deterministic and does *not* utilize LLMs. Checks evaluate:
1. All linked tasks are fully complete.
2. Release notes exist.
3. Workflows are fully inactive.
4. Target environment exists.
5. Environment is healthy via mock probe.

## Approval Flow
Users request approvals -> Approvals undergo RBAC verification -> Approvable only by designated members.
Audit events are appended at each boundary (`RELEASE_APPROVAL_REQUESTED`, `RELEASE_APPROVED`, `RELEASE_PROMOTED`, `RELEASE_ROLLED_BACK`).

## Deployment operations Dashboard
Accessible via `/releases/operations`. It lists all active release deployments across the entire platform, giving operators a bird's eye view.
