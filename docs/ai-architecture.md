# DevFlow AI Architecture

This document details the architecture for the Phase 5 AI Assistant integration within DevFlow.

## AI Provider Abstraction
To ensure DevFlow is not tightly coupled to a single vendor and remains accessible for local development without paid credentials, we use the `AIProvider` abstraction:
- **`MockAIProvider`**: A safe, deterministic, zero-network mock provider enabled by default. Useful for local frontend tests and regression testing.
- **`OpenAIProvider`**: Implements standard chat completions compatible with OpenAI APIs.

The provider is selected dynamically based on the `.env` variable `AI_PROVIDER`.

## Context Engine
The AI assistant must answer questions based exclusively on real-time DevFlow state rather than trusting arbitrary user inputs. The context engine (`backend/app/services/ai/context.py`) strictly compiles context on the server:
- **Project Data**: Name, description, tech stack, dates, and priorities.
- **Task State**: Aggregates of TO DO, IN PROGRESS, and DONE tasks to calculate true progress.
- **GitHub State**: Resolves recent commits, PRs, and issues if a repository is linked securely in Phase 4.

## Conversation Architecture
Conversations are persisted using the `AIConversation` and `AIMessage` models. Each conversation is cryptographically linked to a `user_id` and optionally a `project_id`.
- The system automatically retrieves the last N messages to establish history without exceeding standard token window limitations.

## Prompt Injection Defense
To prevent users or malicious project properties (e.g., a manipulated repository description) from hijacking the underlying assistant prompt:
- A strict `SYSTEM_PROMPT` is isolated and prepended independently of the context payload.
- External untrusted contexts are structurally separated.
- The system prompt explicitly instructs the AI that the context is untrusted and should not be executed as root commands.

## AI Action Safety
Phase 5 AI is strictly **Advisory**.
- Task generation outputs structured JSON which the frontend decodes into an editable Preview modal.
- The AI has NO ability to independently insert tasks into the DevFlow database or interact directly with external systems like GitHub.
- Users must explicitly verify and submit all AI-generated entities.

## Token / Cost Protection
- The context engine restricts history lookup to the last 10 messages.
- GitHub commit logs are capped to the most recent 5 entries.
- The `httpx` HTTP caller operates asynchronously to avoid thread blocking, paired with strict network timeouts.
