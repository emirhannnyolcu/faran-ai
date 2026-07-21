# FARAN - OpenAI Build Week Package

## Submission Description

FARAN is a personal AI workspace and Second Brain that turns a goal into a grounded,
durable workflow. A Planner understands the outcome, Research decides whether stored
evidence is needed, Task creates an execution path, Memory retrieves and preserves
context, Reasoning validates the result, and Writer returns one useful answer. Work can
run immediately, through an API trigger, or on a schedule, and every completed run can
be evaluated and improved from expert corrections.

## Why It Is Different

Most assistants forget the work after answering. FARAN treats every goal as a durable
object: it records execution state, semantic memory, idea connections, completion
criteria, retries, and evaluation evidence. The next workflow can continue with both
FARAN memory and GPT-5.6 persisted reasoning context.

## Demo Script

1. Open `/demo` and enter: "Son üç aydaki öğrenme notlarımı karşılaştır ve gelecek hafta için uygulanabilir bir plan oluştur."
2. Show Planner -> Research -> Task -> Memory -> Writer progress.
3. Open the result and ordered task list.
4. Open Memory and show the persisted `goal_workflow` or `agent_workflow` record.
5. Submit a follow-up with the same conversation ID to demonstrate continuity.
6. Show `/docs`, the queued workflow endpoint, schedule endpoint, and agent eval.
7. Submit an expert correction and show the generated targeted regression case.

## GPT-5.6 Usage

- Sol: quality-critical multi-agent planning, reasoning, and tool use
- Luna: bounded structured note extraction
- Responses API and OpenAI Agents SDK
- Persisted reasoning with response chaining
- Prompt caching and server-side context compaction
- Strict structured outputs and function tools
- OpenAI tracing with sensitive payload capture disabled by default

## Intentional Safety Decisions

Programmatic Tool Calling is not used for FARAN's adaptive, side-effecting workspace
flow. OpenAI guidance recommends it for bounded read-only aggregation; FARAN's current
memory ranking is already deterministic and cheaper in application code. The remote
MCP boundary supports `allowed_callers` so a future measured read-only aggregation can
adopt PTC without exposing write tools.

Computer Use is intentionally disabled because FARAN does not yet have a concrete,
permissioned desktop action with an approval/resume UX. Adding a tool only to claim a
Build Week keyword would weaken the product's security boundary.

## Validation Evidence

- Deterministic end-to-end workflow tests
- Mocked OpenAI SDK handoff, structured output, response chaining, and persistence tests
- Durable queue, worker, schedule, migration, security, and API tests
- Memory, retrieval, agent completion, and correction-regression evaluations
- Desktop and mobile `/demo` visual smoke checks

## External Verification Required

The repository cannot prove live model entitlement, connector OAuth, tracing delivery,
latency, token usage, or billing without project-owned OpenAI credentials. Before
submission, run the credentialed smoke checklist in `docs/LIVE_SMOKE_TEST.md`.
