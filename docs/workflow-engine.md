# Workflow Engine (Phase 29)

DevFlow supports advanced configurable business-processes through the Workflow Engine.

## Architecture

The workflow engine relies on several models to form a robust state machine mechanism:
- `Workflow`: Defines the overarching business process entity mapped to `TASK`, `CLIENT_REQUEST`, `RELEASE`, `DEPLOYMENT`, etc.
- `WorkflowState`: Ordered nodes representing conditions in the business process.
- `WorkflowTransition`: Defining directed edges from one state to another.
- `WorkflowCondition`: Rules evaluated strictly against authorized properties (no `eval()` use).
- `WorkflowAction`: Safe integration hooks referencing the DevFlow Automation Engine (Phase 15) to trigger tasks, comments, and webhooks.
- `WorkflowApproval`: Lightweight, inline gatekeeping without requiring external queue infrastructure like Celery/RabbitMQ.

## AI Workflow Generation

Workflow templates can be mocked and scaffolded using the DevFlow MockAIProvider `generate_workflow()` endpoint. AI generated outputs are strictly validated via Pydantic and never evaluated directly into database execution without explicit user opt-in and sanity checks.

## Security Boundaries

Client visibility natively respects the `organization_id` boundary constraints introduced during the Client Portal Phase 28 iteration. External clientele will only have read views exposed over explicitly "client_visible" attributes, completely abstracting the backend transition states out of purview.
