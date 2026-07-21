import json

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.memory.schemas import MemoryCandidate
from app.memory.service import MemoryService
from app.repositories.memory_connection_repository import MemoryConnectionRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.memory_vector_repository import MemoryVectorRepository
from app.services.context_service import ContextAssemblyService
from app.services.memory_query_service import MemoryQueryService
from app.services.reflection_service import ReflectionService
from app.services.retrieval_service import SemanticRetrievalService
from app.schemas.context import ContextAssemblyResponse
from app.schemas.reflection import ReflectionResponse
from app.schemas.retrieval import SemanticSearchResponse
from app.schemas.agent import GoalAnalysis, PlannedTask, ResearchResult
from app.models.memory_connection import MemoryConnection
from app.models.memory_item import MemoryItem
from app.tools.registry import ToolDefinition, ToolRegistry


class StrictToolArguments(BaseModel):
    """Base contract for strict model-facing tool arguments."""

    model_config = ConfigDict(extra="forbid")


class SearchMemoryArguments(StrictToolArguments):
    """Validated arguments for semantic memory search."""

    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


class AssembleContextArguments(StrictToolArguments):
    """Validated arguments for context assembly."""

    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


class ReflectMemoryArguments(StrictToolArguments):
    """Arguments for whole-memory reflection."""


class ListMemoryConnectionsArguments(StrictToolArguments):
    """Validated arguments for idea-connection lookup."""

    memory_id: int = Field(ge=1)


class SaveGoalMemoryArguments(StrictToolArguments):
    """Validated goal workflow payload written to long-term memory."""

    source_id: int = Field(ge=1)
    goal_analysis: GoalAnalysis
    plan: list[str] = Field(min_length=1, max_length=20)
    tasks: list[PlannedTask] = Field(min_length=1, max_length=20)
    research: ResearchResult | None = None


def build_memory_query_service(db: Session) -> MemoryQueryService:
    """Build memory query service for tools."""
    return MemoryQueryService(
        memory_repository=MemoryRepository(db),
        connection_repository=MemoryConnectionRepository(db),
    )


def search_memory(
    db: Session,
    query: str,
    limit: int = 5,
) -> SemanticSearchResponse:
    """Search long-term memory semantically."""
    return SemanticRetrievalService(
        memory_repository=MemoryRepository(db),
        vector_repository=MemoryVectorRepository(db),
    ).search(query=query, limit=limit)


def assemble_context(
    db: Session,
    query: str,
    limit: int = 5,
) -> ContextAssemblyResponse:
    """Assemble memory context for a query."""
    return ContextAssemblyService(build_memory_query_service(db)).assemble(
        query=query,
        limit=limit,
    )


def reflect_memory(db: Session) -> ReflectionResponse:
    """Reflect over long-term memory."""
    return ReflectionService(build_memory_query_service(db)).reflect()


def list_memory_connections(
    db: Session,
    memory_id: int,
) -> list[tuple[MemoryConnection, MemoryItem]]:
    """List idea connections for a memory item."""
    return build_memory_query_service(db).list_connections(memory_id)


def save_goal_memory(
    db: Session,
    source_id: int,
    goal_analysis: dict[str, object],
    plan: list[str],
    tasks: list[dict[str, object]],
    research: dict[str, object] | None = None,
) -> MemoryItem:
    """Persist one completed goal-planning workflow in long-term memory."""
    analysis = GoalAnalysis.model_validate(goal_analysis)
    planned_tasks = [PlannedTask.model_validate(task) for task in tasks]
    research_result = (
        ResearchResult.model_validate(research) if research is not None else None
    )
    content = json.dumps(
        {
            "goal_analysis": analysis.model_dump(mode="json"),
            "plan": plan,
            "tasks": [task.model_dump(mode="json") for task in planned_tasks],
            "research": (
                research_result.model_dump(mode="json")
                if research_result is not None
                else None
            ),
        },
        ensure_ascii=True,
    )
    candidate = MemoryCandidate(
        source_type="goal_workflow",
        source_id=source_id,
        source_title=analysis.goal[:255],
        source_content=content,
        summary=analysis.objective,
        topic=analysis.topic,
        tags=["goal", "plan", "task"],
        importance=4,
        insights=(
            f"The goal was converted into {len(planned_tasks)} actionable tasks "
            "and is ready for progress tracking."
        ),
    )
    return MemoryService(MemoryRepository(db)).persist_candidate(candidate)


def build_default_tool_registry() -> ToolRegistry:
    """Return FARAN's default internal tool registry."""
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="search_memory",
            description="Search long-term memory by semantic similarity.",
            handler=search_memory,
            arguments_model=SearchMemoryArguments,
        )
    )
    registry.register(
        ToolDefinition(
            name="assemble_context",
            description="Assemble relevant memories into a context package.",
            handler=assemble_context,
            arguments_model=AssembleContextArguments,
        )
    )
    registry.register(
        ToolDefinition(
            name="reflect_memory",
            description="Summarize recurring long-term memory patterns.",
            handler=reflect_memory,
            arguments_model=ReflectMemoryArguments,
        )
    )
    registry.register(
        ToolDefinition(
            name="list_memory_connections",
            description="List stored idea connections for a memory.",
            handler=list_memory_connections,
            arguments_model=ListMemoryConnectionsArguments,
        )
    )
    registry.register(
        ToolDefinition(
            name="save_goal_memory",
            description="Save a planned goal and its tasks to long-term memory.",
            handler=save_goal_memory,
            arguments_model=SaveGoalMemoryArguments,
        )
    )
    return registry
