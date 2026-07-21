from fastapi import APIRouter, Depends

from app.api.dependencies import get_context_assembly_service
from app.schemas.context import ContextAssemblyRequest, ContextAssemblyResponse
from app.services.context_service import ContextAssemblyService


router = APIRouter(prefix="/context", tags=["Context"])


@router.post("/assemble", response_model=ContextAssemblyResponse)
def assemble_context(
    request: ContextAssemblyRequest,
    service: ContextAssemblyService = Depends(get_context_assembly_service),
) -> ContextAssemblyResponse:
    """Assemble memory context for a query."""
    return service.assemble(query=request.query, limit=request.limit)
