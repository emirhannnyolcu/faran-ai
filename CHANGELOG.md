# Changelog

## 2026-07-21 - Build Week hardening

- Added explicit GPT-5.6 Sol/Luna workload roles and strict structured note output.
- Added persisted reasoning, response chaining, compaction, retry, and prompt-cache settings.
- Added structured Workspace Agent output and OpenAI workflow memory persistence.
- Added durable queued workflows, polling, worker execution, and scheduled triggers.
- Added allowlisted OpenAI connector and remote MCP integration boundaries.
- Added workflow completion evals and correction-to-regression persistence.
- Added Build Week workspace UI, demo script, live smoke checklist, and agent diagrams.
- Added workflow conversation, feedback, and schedule migrations.
- Added OpenAI embedding provider with timeout, retry, and safe provider errors.
- Added strict Pydantic schemas for model-facing memory tools.
- Added OpenAI Agents SDK runtime with handoff, specialist agents, and tracing controls.
- Added recoverable workflow attempts and a bounded retry endpoint.
- Added production configuration validation and API-key authentication.
- Added request rate and size limits, security headers, and JSON logs.
- Added labeled retrieval hit-rate and mean-reciprocal-rank evaluations.
- Added Docker packaging, migration-first startup, and GitHub Actions CI.
- Added verified adoption for databases originally created with SQLAlchemy `create_all`.
- Corrected architecture documentation that described implemented vector features as absent.

## 0.1.0 - Production foundation pass

- Added Memory Engine v1 foundation with normalized memory candidates.
- Added persistent `memory_items` model and Alembic migration.
- Added Alembic migration infrastructure and explicit migration docs.
- Added AI provider abstraction with Groq provider implementation.
- Added Embedding Pipeline with canonical memory documents and local vectors.
- Added Idea Connections v1 with persisted memory connection discovery.
- Added Connection API v1 and Memory Timeline API.
- Added Context Assembly v1.
- Added Reflection v1.
- Added SQLite Vector DB v1 and Semantic Retrieval API.
- Added OpenAI GPT-5.6 provider support.
- Added internal tool registry for programmatic tool calls.
- Added multi-agent workflow foundation and `/agent/run`.
- Added `workflow_runs` persistence and migration.
- Added lightweight evaluation service and `/evaluations/smoke`.
- Added no-op memory indexing and retrieval ports for future semantic search.
- Routed note AI metadata through the memory service before persistence.
- Added tests for Memory Engine candidate creation.
- Removed exposed API key from local `.env` and added `.env.example`.
- Added `.gitignore` for secrets, caches, venvs, and local databases.
- Split note handling into route, service, and repository layers.
- Added Pydantic request/response schemas and AI analysis schema.
- Added AI timeout, retry, credential, JSON, and validation handling.
- Added FastAPI exception handlers for domain, provider, and unknown errors.
- Added request middleware with request ID and process time headers.
- Added application logging configuration.
- Moved table creation into FastAPI lifespan startup.
- Added pytest setup with API and AI service tests.
- Cleaned runtime and development requirements.
