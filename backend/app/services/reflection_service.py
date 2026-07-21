from collections import Counter

from app.models.memory_item import MemoryItem
from app.schemas.reflection import ReflectionResponse
from app.services.memory_query_service import MemoryQueryService


class ReflectionService:
    """Generate deterministic reflections from long-term memory."""

    def __init__(self, memory_query_service: MemoryQueryService) -> None:
        self.memory_query_service = memory_query_service

    def reflect(self) -> ReflectionResponse:
        """Return recurring patterns from stored memories."""
        memories = self.memory_query_service.list_memories()
        topics = Counter(memory.topic for memory in memories if memory.topic)
        tags = Counter(tag for memory in memories for tag in _tags(memory))
        high_importance = [
            memory.topic
            for memory in memories
            if memory.importance >= 4 and memory.topic
        ]

        recurring_topics = [topic for topic, count in topics.most_common(5) if count >= 1]
        recurring_tags = [tag for tag, count in tags.most_common(5) if count >= 1]
        high_importance_themes = list(dict.fromkeys(high_importance))[:5]

        return ReflectionResponse(
            total_memories=len(memories),
            recurring_topics=recurring_topics,
            recurring_tags=recurring_tags,
            high_importance_themes=high_importance_themes,
            insight=_insight(recurring_topics, recurring_tags, len(memories)),
        )


def _tags(memory: MemoryItem) -> list[str]:
    return [tag.strip() for tag in (memory.tags or "").split(",") if tag.strip()]


def _insight(topics: list[str], tags: list[str], total: int) -> str:
    if total == 0:
        return "FARAN does not have enough long-term memory to reflect yet."
    if topics and tags:
        return (
            f"Your current memory pattern centers on {topics[0]} "
            f"with recurring signals around {tags[0]}."
        )
    if topics:
        return f"Your current memory pattern centers on {topics[0]}."
    return "Your memories are forming, but no strong pattern has emerged yet."
