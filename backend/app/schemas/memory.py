from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemoryItemRead(BaseModel):
    id: int
    source_type: str
    source_id: int | None = None
    source_title: str
    source_content: str
    summary: str
    topic: str
    tags: str | None = None
    importance: int
    insights: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryConnectionRead(BaseModel):
    id: int
    source_memory_id: int
    target_memory_id: int
    score: float
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryConnectionDetail(BaseModel):
    connection: MemoryConnectionRead
    target_memory: MemoryItemRead
