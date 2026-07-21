# FARAN - Devpost Submission

## Submission Fields

**Project name:** FARAN

**Tagline:** An AI Second Brain that turns goals into researched, durable plans and long-term memory.

**Track:** Work & Productivity

**Codex Session ID:** `019f6f8a-869f-7283-8af2-46e25c86a483`

## Inspiration

AI assistants are useful in the moment, but most of their work disappears after the
answer. People still have to translate goals into plans, reconnect prior knowledge,
track execution, and preserve what was learned. FARAN was created to make that entire
cycle one coherent workspace instead of another chat window.

## What It Does

FARAN turns a natural-language goal into a durable multi-agent workflow. A Planner
frames the outcome, Research decides when existing evidence is needed, Memory retrieves
relevant long-term context, Task creates an ordered execution path, Reasoning checks the
result, and Writer returns one useful response. The plan, tasks, evidence, workflow
state, and final result remain available for future retrieval.

The workspace also supports semantic memory search, idea connections, queued and
scheduled workflows, retryable execution, response continuity, and evaluation from
expert corrections. The interface exposes the useful outcome while keeping model and
infrastructure details out of the user's way.

## How We Built It

FARAN is a FastAPI application organized around route, service, repository, agent, and
tool boundaries. The production agent path uses the OpenAI Agents SDK and Responses API
with GPT-5.6 Sol for quality-critical orchestration and GPT-5.6 Luna for bounded
structured analysis. Agent handoffs, strict Pydantic outputs, function tools, persisted
response IDs, prompt caching, reasoning controls, and context compaction form the core
AI runtime.

Long-term memory is stored in SQLite for this single-workspace build. A provider-neutral
embedding port, vector records, deterministic retrieval, and explicit memory types keep
the design ready for a dedicated vector store later. Durable workflow records support
queueing, bounded retries, leases, recovery, and a separate worker. Alembic manages the
schema, structured logging captures operations, and the test suite covers the API,
agents, memory, migrations, security, tools, and workflow contracts.

## How We Used Codex

Codex was the primary engineering partner throughout Build Week. It audited the original
FastAPI project, separated application layers, implemented and tested the memory and
agent boundaries, integrated the OpenAI runtime, traced failures against live GPT-5.6
runs, repaired agent handoffs, built the workspace UI, and repeatedly ran the complete
test and visual verification loops. Human product direction and architecture decisions
were preserved while Codex handled repository-wide implementation and validation.

## How We Used GPT-5.6

- GPT-5.6 Sol coordinates the goal-to-result agent workflow.
- GPT-5.6 Luna produces schema-validated analysis for bounded extraction tasks.
- The Responses API preserves continuation through `previous_response_id`.
- OpenAI Agents SDK handoffs coordinate specialized agents and function tools.
- Reasoning effort, context retention, prompt caching, and compaction are explicit.
- Provider and model failures are bounded by timeout, retry, validation, and controlled errors.

## Challenges

The hardest part was making agentic behavior durable without turning the system into an
uncontrolled chain of prompts. FARAN needed clear ownership for planning, research,
memory, tasks, reasoning, and writing while preserving one comprehensible response. We
also had to keep long-running work recoverable and make model output safe at every
application boundary.

## Accomplishments

- A real GPT-5.6 multi-agent workflow with structured handoffs and tools
- Long-term memory, semantic retrieval, and automatically discovered idea connections
- Durable queued and scheduled execution with retry and recovery
- Evaluation and correction-to-regression capture
- A focused bilingual Second Brain workspace instead of a generic chatbot UI
- 73 automated tests covering the critical architecture and workflow contracts

## What We Learned

Agent count is not intelligence. The useful result comes from narrow responsibilities,
typed contracts, explicit tool boundaries, durable state, and evaluation. Memory is also
more than a transcript: it must be classified, retrievable, connected, and useful to the
next decision.

## What's Next

The next stage is a permissioned action layer, stronger retrieval evaluation, PostgreSQL
and a dedicated vector store for multi-user scale, and approval-aware integrations for
calendar, files, and workspace tools. Computer Use will only be introduced when FARAN
has an explicit approval and resume experience for real desktop actions.

## Built With

Python, FastAPI, OpenAI Agents SDK, OpenAI Responses API, GPT-5.6 Sol, GPT-5.6 Luna,
Pydantic, SQLAlchemy, Alembic, SQLite, pytest, HTML, CSS, and JavaScript.

## Judge Setup

1. Copy `backend/.env.example` to `backend/.env` and add an OpenAI API key.
2. From `backend`, install `requirements-dev.txt` and run `alembic upgrade head`.
3. Start `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
4. Open `http://127.0.0.1:8000/demo` and submit a goal.
5. Run `python -m pytest -q` to verify the complete test suite.

Never commit or share `backend/.env`; it is ignored by Git.
