from typing import Protocol

from openai import APIError, APITimeoutError, OpenAI

from app.core.settings import settings
from app.prompts.note_analysis import NOTE_ANALYSIS_SYSTEM_PROMPT
from app.schemas.ai import NoteAnalysis
from app.services.errors import AIServiceError


class NoteAnalysisProvider(Protocol):
    """Provider contract for note analysis."""

    def analyze_note(self, content: str) -> str:
        """Return the raw provider response for a note analysis request."""


class GroqNoteAnalysisProvider:
    """Groq provider using the OpenAI-compatible chat completions API."""

    def _get_client(self) -> OpenAI:
        if not settings.GROQ_API_KEY:
            raise AIServiceError("AI provider credentials are not configured")

        return OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            timeout=settings.AI_TIMEOUT_SECONDS,
            max_retries=settings.AI_MAX_RETRIES,
        )

    def analyze_note(self, content: str) -> str:
        """Return raw JSON text from the configured Groq model."""
        try:
            response = self._get_client().chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": NOTE_ANALYSIS_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": content,
                    },
                ],
                temperature=0.2,
            )
        except APITimeoutError as exc:
            raise AIServiceError("AI provider request timed out") from exc
        except APIError as exc:
            raise AIServiceError("AI provider request failed") from exc

        raw_content = response.choices[0].message.content
        if not raw_content:
            raise AIServiceError("AI provider returned an empty response")

        return raw_content


class OpenAINoteAnalysisProvider:
    """OpenAI provider using the Responses API and GPT-5.6 family."""

    def _get_client(self) -> OpenAI:
        if not settings.OPENAI_API_KEY:
            raise AIServiceError("OpenAI provider credentials are not configured")

        return OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.AI_TIMEOUT_SECONDS,
            max_retries=settings.AI_MAX_RETRIES,
        )

    def analyze_note(self, content: str) -> str:
        """Return raw JSON text from the configured OpenAI model."""
        try:
            response = self._get_client().responses.create(
                model=settings.OPENAI_ANALYSIS_MODEL,
                instructions=NOTE_ANALYSIS_SYSTEM_PROMPT,
                input=content,
                reasoning={"effort": "low", "context": "current_turn"},
                prompt_cache_options={
                    "mode": settings.OPENAI_PROMPT_CACHE_MODE,
                    "ttl": "30m",
                },
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "note_analysis",
                        "schema": NoteAnalysis.model_json_schema(),
                        "strict": True,
                    }
                },
                store=False,
            )
        except APITimeoutError as exc:
            raise AIServiceError("AI provider request timed out") from exc
        except APIError as exc:
            raise AIServiceError("AI provider request failed") from exc

        raw_content = getattr(response, "output_text", None)
        if not raw_content:
            raise AIServiceError("AI provider returned an empty response")

        return raw_content


def get_note_analysis_provider() -> NoteAnalysisProvider:
    """Return the configured note analysis provider."""
    provider = settings.AI_PROVIDER.lower()
    if provider == "groq":
        return GroqNoteAnalysisProvider()
    if provider == "openai":
        return OpenAINoteAnalysisProvider()

    raise AIServiceError("Unsupported AI provider")
