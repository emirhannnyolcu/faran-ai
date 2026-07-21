MVP Scope
=========

FARAN's current MVP is a backend foundation for AI-assisted note analysis.

In scope
--------

- Create notes through the API.
- Analyze notes through the configured AI provider.
- Store original note content and AI metadata in SQLite.
- Normalize AI metadata through Memory Engine v1 before persistence.
- Generate canonical embedding documents and local deterministic vectors.
- Discover and persist related idea connections between memories.
- Assemble relevant context from primary, connected, and important memories.
- Reflect recurring themes from long-term memory.
- Store local vectors and search memory semantically.
- Keep AI provider calls behind a provider contract.
- Run a memory-first multi-agent workflow through `/agent/run`.
- Persist workflow state for agent runs.
- Run lightweight memory quality evaluations.
- Run labeled semantic retrieval evaluations.
- Select deterministic or OpenAI Agents SDK execution by configuration.
- Retry bounded failed workflow attempts.
- List, retrieve, and delete notes.
- Keep the codebase testable and ready for Memory Engine work.

Out of scope for this phase
---------------------------

- New user-facing features.
- Frontend implementation.
- User-facing semantic search.
- User-facing connection graph.
- Computer Use automation.
- Multi-user accounts and tenant isolation.
- Distributed background workflow workers.

Quality bar
-----------

- Small layered architecture.
- Explicit request and response schemas.
- Controlled AI and persistence errors.
- Automated tests for the core API path.
- Alembic migrations for schema changes.
- No secrets committed to the repository.
