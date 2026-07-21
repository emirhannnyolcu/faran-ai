import time
from collections.abc import Awaitable, Callable
from fastapi import Request, Response

from app.core.logging import get_logger
from app.core.security import normalized_request_id


logger = get_logger(__name__)


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach request metadata and emit one access log entry per request."""
    request_id = normalized_request_id(request.headers.get("X-Request-ID"))
    request.state.request_id = request_id
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    logger.info(
        "HTTP request completed",
        extra={
            "http_method": request.method,
            "http_path": request.url.path,
            "status_code": response.status_code,
            "request_id": request_id,
            "duration_seconds": round(process_time, 6),
        },
    )
    return response
