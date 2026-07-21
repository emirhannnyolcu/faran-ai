from fastapi import APIRouter, Depends

from app.api.dependencies import get_semantic_retrieval_service
from app.schemas.retrieval import SemanticSearchRequest, SemanticSearchResponse
from app.services.retrieval_service import SemanticRetrievalService


router = APIRouter(prefix="/retrieval", tags=["Retrieval"])


@router.post("/semantic-search", response_model=SemanticSearchResponse)
def semantic_search(
    request: SemanticSearchRequest,
    service: SemanticRetrievalService = Depends(get_semantic_retrieval_service),
) -> SemanticSearchResponse:
    """Search long-term memory by semantic similarity."""
    return service.search(query=request.query, limit=request.limit)
