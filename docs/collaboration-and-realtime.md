# Advanced Collaboration & Real-Time Workspace (Phase 14)

DevFlow Phase 14 transforms the platform into an active engineering collaboration hub. 

## Features
- **Project Discussions**: Threaded conversations isolated by organization and project.
- **Task Comments**: Threaded replies, emoji reactions, edit history, and pinning capabilities.
- **Global Search (`Cmd+K`)**: Rapid navigation and full-text search across all workspaces, tasks, discussions, and releases.
- **Command Palette**: Included within the Global Search modal, allowing users to rapidly jump to create flows or navigate to deep settings.
- **WebSocket Real-time Feed**: Real-time event propagation via `useRealtime` hook for live updates across browser instances.
- **Mentions**: Typing `@` alerts users, linking directly into the notification center.
- **Collaboration Analytics**: Measure and visualize team collaboration activity (response times, active contributors, total volume).

## Architecture Details
- Models: `Comment`, `Discussion`, `CommentReaction`, `Attachment`.
- The real-time system uses `ConnectionManager` to isolate websockets by `organization_id`.
- The `GlobalSearch` acts as an omni-channel lookup system mapping strictly to user's permissions and org bounds.
- All AI functionalities strictly append into a read-only or advisory state, honoring DevFlow's 'AI as a Co-pilot' ethos.

## Security
- `X-Organization-Id` validations happen inside the WebSocket upgrade endpoint to ensure total multi-tenant safety.
- Comments map `entity_id` and `entity_type` generically, allowing easy extension to Sprints, Pipelines, etc., without table bloat.
