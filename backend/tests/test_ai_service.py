import pytest

from app.services.ai_service import _parse_analysis_response, analyze_note
from app.services.errors import AIServiceError


class FakeProvider:
    def analyze_note(self, content: str) -> str:
        return """
        {
            "summary": "Provider summary",
            "topic": "Provider topic",
            "tags": ["provider"],
            "importance": 2,
            "ai_insights": "Provider insight"
        }
        """


def test_parse_analysis_response_accepts_valid_json():
    analysis = _parse_analysis_response(
        """
        {
            "summary": "Summary",
            "topic": "Topic",
            "tags": ["ai", "memory"],
            "importance": 5,
            "ai_insights": "Insight"
        }
        """
    )

    assert analysis.summary == "Summary"
    assert analysis.tags == ["ai", "memory"]
    assert analysis.importance == 5


@pytest.mark.parametrize(
    "payload",
    [
        "not-json",
        '{"summary": "Summary"}',
        '{"summary": "Summary", "topic": "Topic", "tags": "ai", "importance": 5, "ai_insights": "Insight"}',
        '{"summary": "Summary", "topic": "Topic", "tags": ["ai"], "importance": 9, "ai_insights": "Insight"}',
    ],
)
def test_parse_analysis_response_rejects_invalid_payloads(payload):
    with pytest.raises(AIServiceError):
        _parse_analysis_response(payload)


def test_analyze_note_requires_provider_credentials(monkeypatch):
    monkeypatch.setattr("app.ai.providers.settings.AI_PROVIDER", "groq")
    monkeypatch.setattr("app.ai.providers.settings.GROQ_API_KEY", "")

    with pytest.raises(AIServiceError) as exc_info:
        analyze_note("A note")

    assert exc_info.value.message == "AI provider credentials are not configured"


def test_openai_provider_requires_credentials(monkeypatch):
    monkeypatch.setattr("app.ai.providers.settings.AI_PROVIDER", "openai")
    monkeypatch.setattr("app.ai.providers.settings.OPENAI_API_KEY", "")

    with pytest.raises(AIServiceError) as exc_info:
        analyze_note("A note")

    assert exc_info.value.message == "OpenAI provider credentials are not configured"


def test_analyze_note_accepts_injected_provider():
    analysis = analyze_note("A note", provider=FakeProvider())

    assert analysis.summary == "Provider summary"
    assert analysis.topic == "Provider topic"
    assert analysis.tags == ["provider"]
    assert analysis.importance == 2
