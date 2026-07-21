from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.agent import router as agent_router
from app.api.exception_handlers import (
    ai_service_exception_handler,
    note_not_found_exception_handler,
    memory_not_found_exception_handler,
    note_persistence_exception_handler,
    unhandled_exception_handler,
    workflow_not_found_exception_handler,
    workflow_retry_not_allowed_exception_handler,
    workflow_schedule_not_found_exception_handler,
)
from app.api.context import router as context_router
from app.api.evaluations import router as evaluations_router
from app.api.memory import router as memory_router
from app.api.notes import router as notes_router
from app.api.reflection import router as reflection_router
from app.api.retrieval import router as retrieval_router
from app.core.database import Base, engine
from app.core.logging import configure_logging
from app.core.middleware import request_context_middleware
from app.core.security import security_middleware
from app.core.settings import BASE_DIR, settings
from app.models.memory_connection import MemoryConnection
from app.models.memory_item import MemoryItem
from app.models.memory_vector import MemoryVector
from app.models.note import Note
from app.models.workflow_run import WorkflowRun
from app.models.agent_feedback import AgentFeedback
from app.models.workflow_schedule import WorkflowSchedule
from app.services.errors import (
    AIServiceError,
    WorkflowNotFoundError,
    WorkflowRetryNotAllowedError,
    WorkflowScheduleNotFoundError,
)
from app.services.memory_query_service import MemoryItemNotFoundError
from app.services.note_service import NoteNotFoundError, NotePersistenceError


configure_logging()

STATIC_DIR = BASE_DIR / "app" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize application resources for the current process."""
    settings.validate_runtime()
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if settings.allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    )

app.middleware("http")(security_middleware)
app.middleware("http")(request_context_middleware)
app.include_router(agent_router)
app.include_router(notes_router)
app.include_router(memory_router)
app.include_router(context_router)
app.include_router(reflection_router)
app.include_router(retrieval_router)
app.include_router(evaluations_router)
app.add_exception_handler(AIServiceError, ai_service_exception_handler)
app.add_exception_handler(NoteNotFoundError, note_not_found_exception_handler)
app.add_exception_handler(MemoryItemNotFoundError, memory_not_found_exception_handler)
app.add_exception_handler(NotePersistenceError, note_persistence_exception_handler)
app.add_exception_handler(WorkflowNotFoundError, workflow_not_found_exception_handler)
app.add_exception_handler(
    WorkflowRetryNotAllowedError,
    workflow_retry_not_allowed_exception_handler,
)
app.add_exception_handler(
    WorkflowScheduleNotFoundError,
    workflow_schedule_not_found_exception_handler,
)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": f"{settings.APP_NAME} is running"
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


@app.get("/demo", include_in_schema=False)
def demo() -> FileResponse:
    """Serve FARAN's Build Week workspace experience."""
    return FileResponse(STATIC_DIR / "index.html")
