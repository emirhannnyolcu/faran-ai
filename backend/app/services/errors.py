class AIServiceError(Exception):
    """Raised when note analysis cannot be completed safely."""

    def __init__(self, message: str = "AI analysis failed"):
        self.message = message
        super().__init__(message)


class WorkflowNotFoundError(Exception):
    """Raised when an agent workflow cannot be found."""


class WorkflowRetryNotAllowedError(Exception):
    """Raised when a workflow is not eligible for another attempt."""


class WorkflowScheduleNotFoundError(Exception):
    """Raised when a durable workflow schedule cannot be found."""
