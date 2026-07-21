from fastapi import APIRouter, Depends

from app.api.dependencies import get_memory_query_service
from app.models.memory_item import MemoryItem
from app.schemas.memory import MemoryConnectionDetail, MemoryItemRead
from app.services.memory_query_service import MemoryQueryService


router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/", response_model=list[MemoryItemRead])
def list_memories(
    service: MemoryQueryService = Depends(get_memory_query_service),
) -> list[MemoryItem]:
    """Return FARAN's memory timeline."""
    return service.list_memories()


@router.get("/{memory_id}", response_model=MemoryItemRead)
def get_memory(
    memory_id: int,
    service: MemoryQueryService = Depends(get_memory_query_service),
) -> MemoryItem:
    """Return a single memory item."""
    return service.get_memory(memory_id)


@router.get("/{memory_id}/connections", response_model=list[MemoryConnectionDetail])
def list_memory_connections(
    memory_id: int,
    service: MemoryQueryService = Depends(get_memory_query_service),
) -> list[MemoryConnectionDetail]:
    """Return idea connections for a memory item."""
    return [
        MemoryConnectionDetail(connection=connection, target_memory=target)
        for connection, target in service.list_connections(memory_id)
    ]
