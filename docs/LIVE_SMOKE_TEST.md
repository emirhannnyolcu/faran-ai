# Live OpenAI Smoke Test

1. Set `OPENAI_API_KEY`, `AI_PROVIDER=openai`, and `AGENT_RUNTIME=openai`.
2. Run `python -m alembic upgrade head`.
3. Start API and worker.
4. Submit one note and verify strict GPT-5.6 Luna analysis.
5. Submit a goal with `conversation_id=live-smoke`.
6. Submit a follow-up using the same conversation ID.
7. Confirm both workflows complete and the second has a persisted `response_id` chain.
8. Confirm `agent_workflow`, vector, and idea-connection records exist.
9. Inspect OpenAI tracing and verify sensitive payload capture is disabled.
10. Record latency, input/output/reasoning/cached tokens, cache writes, and total cost.
11. If a connector is configured, test only its explicit read-only allowlist.
12. Run `pytest` again and save the final result for the submission evidence.
