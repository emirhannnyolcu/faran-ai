# FARAN Engineering Guide

## Product boundary

FARAN is a personal AI workspace, Second Brain, and durable multi-agent system.
Changes must improve grounded planning, execution, memory, or evaluation. Do not
add unrelated chatbot or infrastructure features.

## Architecture

- Keep HTTP routes thin: Route -> Service -> Repository.
- Put model prompts in `backend/app/prompts` and validated contracts in schemas.
- Keep provider-specific behavior behind `backend/app/ai` or an orchestrator.
- Side-effecting tools require an explicit allowlist and a product permission path.
- Preserve deterministic runtime behavior for offline development and tests.

## Verification

From `backend` run:

```powershell
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m alembic upgrade head
```

For UI changes, run the server and verify `/demo` at desktop and mobile widths.
Never claim live OpenAI behavior without a credentialed smoke test.
