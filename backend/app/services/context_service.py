from app.models.memory_item import MemoryItem
from app.schemas.context import ContextAssemblyResponse
from app.schemas.memory import MemoryConnectionDetail
from app.services.memory_query_service import MemoryQueryService


class ContextAssemblyService:
    """Assemble relevant long-term memory context for a user query."""

    def __init__(self, memory_query_service: MemoryQueryService) -> None:
        self.memory_query_service = memory_query_service

    def assemble(self, query: str, limit: int = 5) -> ContextAssemblyResponse:
        """Build a deterministic context package from stored memories."""
        memories = self.memory_query_service.list_memories()
        primary_memories = _rank_memories_by_query(query, memories)[:limit]
        connected_memories = self._connections_for(primary_memories, limit=limit)
        high_importance_memories = [
            memory
            for memory in memories
            if memory.importance >= 4 and memory not in primary_memories
        ][:limit]

        return ContextAssemblyResponse(
            query=query,
            primary_memories=primary_memories,
            connected_memories=connected_memories,
            high_importance_memories=high_importance_memories,
            context_text=_build_context_text(
                primary_memories=primary_memories,
                connected_memories=connected_memories,
                high_importance_memories=high_importance_memories,
            ),
        )

    def _connections_for(
        self,
        memories: list[MemoryItem],
        limit: int,
    ) -> list[MemoryConnectionDetail]:
        details: list[MemoryConnectionDetail] = []
        for memory in memories:
            for connection, target in self.memory_query_service.list_connections(memory.id):
                details.append(
                    MemoryConnectionDetail(connection=connection, target_memory=target)
                )
        return details[:limit]


def _rank_memories_by_query(query: str, memories: list[MemoryItem]) -> list[MemoryItem]:
    query_tokens = _tokens(query)
    return sorted(
        memories,
        key=lambda memory: (
            len(query_tokens & _tokens(_memory_text(memory))),
            memory.importance,
            memory.id,
        ),
        reverse=True,
    )


def _build_context_text(
    primary_memories: list[MemoryItem],
    connected_memories: list[MemoryConnectionDetail],
    high_importance_memories: list[MemoryItem],
) -> str:
    lines: list[str] = []
    for memory in primary_memories:
        lines.append(f"Primary memory: {memory.summary} ({memory.topic})")
    for detail in connected_memories:
        lines.append(
            "Connected memory: "
            f"{detail.target_memory.summary} "
            f"[reason={detail.connection.reason}, score={detail.connection.score}]"
        )
    for memory in high_importance_memories:
        lines.append(f"High importance memory: {memory.summary} ({memory.topic})")
    return "\n".join(lines)


def _memory_text(memory: MemoryItem) -> str:
    return " ".join(
        [
            memory.source_title,
            memory.source_content,
            memory.summary,
            memory.topic,
            memory.tags or "",
            memory.insights,
        ]
    )


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in text.split() if len(token) > 2}
