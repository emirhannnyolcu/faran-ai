from agents import ModelSettings
from agents.retry import ModelRetrySettings
from openai.types.shared import Reasoning

from app.core.settings import settings


def build_agent_model_settings() -> ModelSettings:
    """Return explicit GPT-5.6 settings for agentic production workflows."""
    return ModelSettings(
        reasoning=Reasoning(
            effort=settings.OPENAI_REASONING_EFFORT,
            context=settings.OPENAI_REASONING_CONTEXT,
            summary="concise",
        ),
        verbosity=settings.OPENAI_TEXT_VERBOSITY,
        parallel_tool_calls=True,
        truncation="auto",
        store=True,
        prompt_cache_options={
            "mode": settings.OPENAI_PROMPT_CACHE_MODE,
            "ttl": "30m",
        },
        context_management=[
            {
                "type": "compaction",
                "compact_threshold": settings.OPENAI_CONTEXT_COMPACT_THRESHOLD,
            }
        ],
        retry=ModelRetrySettings(max_retries=settings.AI_MAX_RETRIES),
    )
