import logging
import json
from logging.config import dictConfig
from datetime import UTC, datetime

from app.core.settings import settings


class JsonFormatter(logging.Formatter):
    """Format application logs as one JSON object per line."""

    fields = (
        "request_id",
        "http_method",
        "http_path",
        "status_code",
        "duration_seconds",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging() -> None:
    """Configure application-wide structured console logging."""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "app.core.logging.JsonFormatter",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
            },
            "loggers": {
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": settings.LOG_LEVEL,
                    "propagate": False,
                },
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named application logger."""
    return logging.getLogger(name)
