from fastapi import APIRouter, Depends

from app.api.dependencies import get_reflection_service
from app.schemas.reflection import ReflectionResponse
from app.services.reflection_service import ReflectionService


router = APIRouter(prefix="/reflection", tags=["Reflection"])


@router.get("/", response_model=ReflectionResponse)
def get_reflection(
    service: ReflectionService = Depends(get_reflection_service),
) -> ReflectionResponse:
    """Return FARAN's current reflection over stored memories."""
    return service.reflect()
