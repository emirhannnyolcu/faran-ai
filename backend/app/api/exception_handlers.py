from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.services.errors import (
    AIServiceError,
    WorkflowNotFoundError,
    WorkflowRetryNotAllowedError,
    WorkflowScheduleNotFoundError,
)
from app.services.memory_query_service import MemoryItemNotFoundError
from app.services.note_service import NoteNotFoundError, NotePersistenceError


logger = get_logger(__name__)


async def ai_service_exception_handler(
    request: Request,
    exc: AIServiceError,
) -> JSONResponse:
    """Return a safe gateway error for upstream AI failures."""
    return JSONResponse(
        status_code=502,
        content={"detail": exc.message},
    )


async def note_not_found_exception_handler(
    request: Request,
    exc: NoteNotFoundError,
) -> JSONResponse:
    """Return a stable 404 response for missing notes."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Note not found"},
    )


async def memory_not_found_exception_handler(
    request: Request,
    exc: MemoryItemNotFoundError,
) -> JSONResponse:
    """Return a stable 404 response for missing memories."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Memory not found"},
    )


async def note_persistence_exception_handler(
    request: Request,
    exc: NotePersistenceError,
) -> JSONResponse:
    """Return a stable 500 response for persistence failures."""
    logger.exception("Note persistence error on %s", request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


async def workflow_not_found_exception_handler(
    request: Request,
    exc: WorkflowNotFoundError,
) -> JSONResponse:
    """Return a stable 404 response for a missing workflow."""
    return JSONResponse(status_code=404, content={"detail": "Workflow not found"})


async def workflow_retry_not_allowed_exception_handler(
    request: Request,
    exc: WorkflowRetryNotAllowedError,
) -> JSONResponse:
    """Return a stable conflict response for an ineligible retry."""
    return JSONResponse(
        status_code=409,
        content={"detail": "Workflow cannot be retried"},
    )


async def workflow_schedule_not_found_exception_handler(
    request: Request,
    exc: WorkflowScheduleNotFoundError,
) -> JSONResponse:
    """Return a stable 404 response for a missing schedule."""
    return JSONResponse(status_code=404, content={"detail": "Workflow schedule not found"})


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a generic 500 response without leaking internals."""
    logger.exception("Unhandled error on %s", request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
