from pydantic import BaseModel, Field, field_validator

from app.schemas.memory import MemoryItemRead


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def reject_blank_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query cannot be blank")
        return value


class SemanticSearchResult(BaseModel):
    memory: MemoryItemRead
    score: float


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResult]
