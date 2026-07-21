from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    APP_NAME: str = "FARAN AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    AUTO_CREATE_TABLES: bool = True
    DATABASE_URL: str = f"sqlite:///{str(BASE_DIR / 'faran.db').replace('\\', '/')}"
    AUTH_ENABLED: bool = False
    API_ACCESS_KEY: str = ""
    ALLOWED_HOSTS: str = "127.0.0.1,localhost,testserver"
    CORS_ORIGINS: str = ""
    MAX_REQUEST_BODY_BYTES: int = 1_048_576
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    AI_PROVIDER: str = "groq"
    AI_MODEL: str = "llama3-70b-8192"
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.6-sol"
    OPENAI_ANALYSIS_MODEL: str = "gpt-5.6-luna"
    OPENAI_REASONING_EFFORT: Literal[
        "none", "low", "medium", "high", "xhigh", "max"
    ] = "high"
    OPENAI_REASONING_CONTEXT: Literal["current_turn", "all_turns"] = "all_turns"
    OPENAI_TEXT_VERBOSITY: Literal["low", "medium", "high"] = "medium"
    OPENAI_PROMPT_CACHE_MODE: Literal["implicit", "explicit"] = "implicit"
    OPENAI_CONTEXT_COMPACT_THRESHOLD: int = 200_000
    OPENAI_CONNECTOR_ID: str = ""
    OPENAI_CONNECTOR_AUTHORIZATION: str = ""
    OPENAI_CONNECTOR_ALLOWED_TOOLS: str = ""
    OPENAI_MCP_SERVER_URL: str = ""
    OPENAI_MCP_SERVER_LABEL: str = "faran_workspace"
    OPENAI_MCP_ALLOWED_TOOLS: str = ""
    AI_TIMEOUT_SECONDS: float = 20.0
    AI_MAX_RETRIES: int = 2
    AGENT_RUNTIME: str = "deterministic"
    AGENT_MAX_TURNS: int = 12
    AGENT_WORKFLOW_TIMEOUT_SECONDS: float = 180.0
    WORKFLOW_MAX_ATTEMPTS: int = 3
    OPENAI_TRACING_ENABLED: bool = True
    OPENAI_TRACE_INCLUDE_SENSITIVE_DATA: bool = False

    EMBEDDING_PROVIDER: str = "local"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8"
    )

    @property
    def allowed_hosts(self) -> list[str]:
        """Return normalized trusted hosts."""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    @property
    def cors_origins(self) -> list[str]:
        """Return normalized CORS origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def openai_connector_allowed_tools(self) -> list[str]:
        return [
            tool.strip()
            for tool in self.OPENAI_CONNECTOR_ALLOWED_TOOLS.split(",")
            if tool.strip()
        ]

    @property
    def openai_mcp_allowed_tools(self) -> list[str]:
        return [
            tool.strip()
            for tool in self.OPENAI_MCP_ALLOWED_TOOLS.split(",")
            if tool.strip()
        ]

    def validate_runtime(self) -> None:
        """Reject unsafe or incomplete production configuration."""
        if self.ENVIRONMENT.lower() != "production":
            return

        errors: list[str] = []
        if self.DEBUG:
            errors.append("DEBUG must be disabled")
        if self.AUTO_CREATE_TABLES:
            errors.append("AUTO_CREATE_TABLES must be disabled")
        if not self.AUTH_ENABLED or len(self.API_ACCESS_KEY) < 32:
            errors.append("AUTH_ENABLED requires API_ACCESS_KEY with at least 32 characters")
        if not self.allowed_hosts or "*" in self.allowed_hosts:
            errors.append("ALLOWED_HOSTS must explicitly list trusted hosts")
        if self.AI_PROVIDER.lower() == "openai" and not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required for the OpenAI provider")
        if self.AI_PROVIDER.lower() == "groq" and not self.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required for the Groq provider")
        if self.AGENT_RUNTIME.lower() == "openai" and not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required for the OpenAI agent runtime")
        if self.EMBEDDING_PROVIDER.lower() == "openai" and not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required for OpenAI embeddings")
        if self.OPENAI_CONTEXT_COMPACT_THRESHOLD < 10_000:
            errors.append("OPENAI_CONTEXT_COMPACT_THRESHOLD must be at least 10000")
        if self.OPENAI_CONNECTOR_ID and (
            not self.OPENAI_CONNECTOR_AUTHORIZATION
            or not self.openai_connector_allowed_tools
        ):
            errors.append(
                "OpenAI connector requires authorization and an explicit tool allowlist"
            )
        if self.OPENAI_MCP_SERVER_URL and not self.openai_mcp_allowed_tools:
            errors.append("Remote MCP server requires an explicit tool allowlist")
        if errors:
            raise RuntimeError("Invalid production configuration: " + "; ".join(errors))


settings = Settings()
