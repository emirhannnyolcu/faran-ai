from pydantic import BaseModel, Field, field_validator

from app.schemas.memory import MemoryConnectionDetail, MemoryItemRead


class ContextAssemblyRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def reject_blank_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query cannot be blank")
        return value


class ContextAssemblyResponse(BaseModel):
    query: str
    primary_memories: list[MemoryItemRead]
    connected_memories: list[MemoryConnectionDetail]
    high_importance_memories: list[MemoryItemRead]
    context_text: str
