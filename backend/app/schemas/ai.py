from pydantic import BaseModel, Field


class NoteAnalysis(BaseModel):
    summary: str
    topic: str
    tags: list[str]
    importance: int = Field(..., ge=1, le=5)
    ai_insights: str
