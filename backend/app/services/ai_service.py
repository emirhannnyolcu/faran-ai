import json
from json import JSONDecodeError

from pydantic import ValidationError

from app.ai.providers import NoteAnalysisProvider, get_note_analysis_provider
from app.schemas.ai import NoteAnalysis
from app.services.errors import AIServiceError


def _parse_analysis_response(raw_content: str) -> NoteAnalysis:
    result = raw_content.strip()
    result = result.replace("```json", "")
    result = result.replace("```", "")
    result = result.strip()

    try:
        analysis = json.loads(result)
    except JSONDecodeError as exc:
        raise AIServiceError("AI provider returned invalid JSON") from exc

    if not isinstance(analysis, dict):
        raise AIServiceError("AI provider returned an unexpected response")

    try:
        return NoteAnalysis.model_validate(analysis)
    except ValidationError as exc:
        raise AIServiceError("AI provider returned an invalid analysis") from exc


def analyze_note(
    content: str,
    provider: NoteAnalysisProvider | None = None,
) -> NoteAnalysis:
    """Analyze a note with the configured provider and validate the response."""
    provider = provider or get_note_analysis_provider()
    raw_content = provider.analyze_note(content)
    return _parse_analysis_response(raw_content)
