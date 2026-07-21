from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=10000)

    @field_validator("title", "content")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value


class NoteRead(BaseModel):
    id: int
    title: str
    content: str
    summary: str | None = None
    topic: str | None = None
    tags: str | None = None
    importance: int | None = None
    ai_insights: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeleteNoteResponse(BaseModel):
    message: str
