import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.settings import settings
from app.main import app


@pytest.fixture(autouse=True)
def isolate_tests_from_live_agent_runtime(monkeypatch):
    """Prevent ordinary tests from consuming live OpenAI API quota."""
    monkeypatch.setattr(settings, "AGENT_RUNTIME", "deterministic")
    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")


@pytest.fixture()
def client(tmp_path):
    """Return a TestClient backed by an isolated SQLite database."""
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.state.testing_session_factory = TestingSessionLocal

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    del app.state.testing_session_factory
    Base.metadata.drop_all(bind=engine)
