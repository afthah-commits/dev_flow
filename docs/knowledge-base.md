# Knowledge Base & Documentation

The Knowledge Base provides centralized engineering documentation, structured in spaces and hierarchical documents.

## Core Features
1. **Spaces**: Organization-level containers for documents (e.g. "Engineering Handbook", "Architecture").
2. **Documents**: Hierarchical documents written in Markdown. Supports parents/children.
3. **Version History**: Full version tracking and restoration.
4. **Global Search**: Deeply integrated into the `Ctrl+K` DevFlow search.
5. **AI Integration**: Ask questions and generate document summaries.

## Architecture
- `KnowledgeSpace`: Top-level container.
- `KnowledgeDocument`: Markdown nodes (draft/published).
- `KnowledgeDocumentVersion`: Immutable history of changes.

## Usage
- Open **Knowledge Base** from the global search or sidebar.
- Use `Ctrl+K` to search through knowledge base documents.
- Use the **Ask AI** feature inside spaces to query your engineering context.
