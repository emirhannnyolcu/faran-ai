from pydantic import BaseModel


class ReflectionResponse(BaseModel):
    total_memories: int
    recurring_topics: list[str]
    recurring_tags: list[str]
    high_importance_themes: list[str]
    insight: str
