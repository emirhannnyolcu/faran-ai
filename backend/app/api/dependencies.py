from fastapi import Depends
from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentOrchestrator
from app.agents.openai_orchestrator import OpenAIAgentOrchestrator
from app.core.database import get_db
from app.core.settings import settings
from app.evaluations.service import EvaluationService
from app.repositories.memory_connection_repository import MemoryConnectionRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.memory_vector_repository import MemoryVectorRepository
from app.services.context_service import ContextAssemblyService
from app.services.memory_query_service import MemoryQueryService
from app.services.note_service import NoteService
from app.services.reflection_service import ReflectionService
from app.services.retrieval_service import SemanticRetrievalService
from app.services.workflow_service import WorkflowService
from app.services.schedule_service import ScheduleService


def get_note_service(db: Session = Depends(get_db)) -> NoteService:
    """Build a note service for the current request."""
    return NoteService(db)


def get_agent_orchestrator(
    db: Session = Depends(get_db),
) -> AgentOrchestrator | OpenAIAgentOrchestrator:
    """Build an agent orchestrator for the current request."""
    if settings.AGENT_RUNTIME.lower() == "openai":
        return OpenAIAgentOrchestrator(db)
    if settings.AGENT_RUNTIME.lower() != "deterministic":
        raise ValueError("Unsupported agent runtime")
    return AgentOrchestrator(db)


def get_workflow_service(db: Session = Depends(get_db)) -> WorkflowService:
    """Build a durable workflow service for the current request."""
    return WorkflowService(db)


def get_schedule_service(db: Session = Depends(get_db)) -> ScheduleService:
    """Build a durable schedule service for the current request."""
    return ScheduleService(db)


def get_memory_query_service(db: Session = Depends(get_db)) -> MemoryQueryService:
    """Build a memory query service for the current request."""
    return MemoryQueryService(
        memory_repository=MemoryRepository(db),
        connection_repository=MemoryConnectionRepository(db),
    )


def get_context_assembly_service(
    memory_query_service: MemoryQueryService = Depends(get_memory_query_service),
) -> ContextAssemblyService:
    """Build a context assembly service for the current request."""
    return ContextAssemblyService(memory_query_service)


def get_reflection_service(
    memory_query_service: MemoryQueryService = Depends(get_memory_query_service),
) -> ReflectionService:
    """Build a reflection service for the current request."""
    return ReflectionService(memory_query_service)


def get_semantic_retrieval_service(
    db: Session = Depends(get_db),
) -> SemanticRetrievalService:
    """Build a semantic retrieval service for the current request."""
    return SemanticRetrievalService(
        memory_repository=MemoryRepository(db),
        vector_repository=MemoryVectorRepository(db),
    )


def get_evaluation_service(
    db: Session = Depends(get_db),
    memory_query_service: MemoryQueryService = Depends(get_memory_query_service),
    retrieval_service: SemanticRetrievalService = Depends(
        get_semantic_retrieval_service
    ),
) -> EvaluationService:
    """Build an evaluation service for the current request."""
    return EvaluationService(memory_query_service, retrieval_service, db)
