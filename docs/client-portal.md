# Client Portal & External Collaboration (Phase 28)

DevFlow allows organizations to collaborate securely with external clients via the Client Portal. 

## Data Model
- `Client`: Represents external entities.
- `ClientUser`: Associates DevFlow users with a specific client.
- `ClientProjectAccess`: Explicitly assigns clients to specific projects.
- `ClientRequest`: Support/feature requests submitted by clients.

## Security Architecture
- Clients are strictly isolated by `organization_id` and explicitly granted project access.
- Internal comments, tasks, and audit logs are hidden by default unless marked `client_visible`.
- Knowledge Base introduces `CLIENTS` and `PUBLIC` visibility to safeguard internal IP.

## API Endpoints
- `GET /api/v1/client-portal/me`: Fetches client context.
- `GET /api/v1/client-portal/{client_id}/projects`: Lists accessible projects.
- `POST /api/v1/client-portal/{client_id}/requests`: Creates new client requests.
- `POST /api/v1/ai/client/summary`: Safely summaries client-visible data using Mock AI.
