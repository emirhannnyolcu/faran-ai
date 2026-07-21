from pydantic import BaseModel, Field


class MemoryCandidate(BaseModel):
    """Normalized memory payload prepared from AI note analysis."""

    source_type: str = "note"
    source_id: int | None = None
    source_title: str
    source_content: str
    summary: str
    topic: str
    tags: list[str] = Field(default_factory=list)
    importance: int = Field(..., ge=1, le=5)
    insights: str

    @property
    def tags_text(self) -> str:
        """Return tags in the current note storage format."""
        return ", ".join(self.tags)
