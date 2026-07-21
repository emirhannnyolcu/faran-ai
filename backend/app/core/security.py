import re
import secrets
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from threading import Lock
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.settings import settings


_PUBLIC_PATHS = {"/", "/health", "/demo", "/docs", "/openapi.json", "/redoc"}
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class SlidingWindowRateLimiter:
    """Bound request volume per client within one application process."""

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Return whether a request is allowed and its retry delay."""
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            timestamps = self._requests[key]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= limit:
                retry_after = max(1, int(window_seconds - (now - timestamps[0])))
                return False, retry_after
            timestamps.append(now)
            return True, 0

    def clear(self) -> None:
        """Clear limiter state for isolated tests."""
        with self._lock:
            self._requests.clear()


rate_limiter = SlidingWindowRateLimiter()


def normalized_request_id(value: str | None) -> str:
    """Accept safe correlation IDs and replace malformed values."""
    if value and _REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())


async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Enforce authentication, size limits, rate limits, and response headers."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            too_large = int(content_length) > settings.MAX_REQUEST_BODY_BYTES
        except ValueError:
            return _with_security_headers(
                JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
            )
        if too_large:
            return _with_security_headers(
                JSONResponse(status_code=413, content={"detail": "Request body too large"})
            )

    is_public = request.url.path in _PUBLIC_PATHS or request.url.path.startswith(
        "/static/"
    )
    if settings.AUTH_ENABLED and not is_public:
        supplied_key = _extract_api_key(request)
        if not supplied_key or not secrets.compare_digest(
            supplied_key,
            settings.API_ACCESS_KEY,
        ):
            return _with_security_headers(
                JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or missing API credentials"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            )

    if settings.RATE_LIMIT_ENABLED and not is_public:
        client_host = request.client.host if request.client else "unknown"
        allowed, retry_after = rate_limiter.allow(
            client_host,
            settings.RATE_LIMIT_REQUESTS,
            settings.RATE_LIMIT_WINDOW_SECONDS,
        )
        if not allowed:
            return _with_security_headers(
                JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": str(retry_after)},
                )
            )

    response = await call_next(request)
    return _with_security_headers(response)


def _with_security_headers(response: Response) -> Response:
    """Apply baseline browser security headers to every response path."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


def _extract_api_key(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token
    return request.headers.get("x-api-key")
