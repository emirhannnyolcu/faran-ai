from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.database import Base


def test_alembic_migrations_create_expected_tables(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setattr("app.core.settings.settings.DATABASE_URL", database_url)

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)

    assert "notes" in inspector.get_table_names()
    assert "memory_items" in inspector.get_table_names()
    assert "memory_connections" in inspector.get_table_names()
    assert "memory_vectors" in inspector.get_table_names()
    assert "workflow_runs" in inspector.get_table_names()
    assert "agent_feedback" in inspector.get_table_names()
    assert "workflow_schedules" in inspector.get_table_names()
    workflow_columns = {
        column["name"] for column in inspector.get_columns("workflow_runs")
    }
    assert {"attempt_count", "max_attempts", "last_error", "started_at", "completed_at"} <= workflow_columns
    assert {"runtime", "conversation_id", "response_id"} <= workflow_columns


def test_alembic_adopts_verified_legacy_create_all_schema(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'legacy.db'}"
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO notes (title, content) VALUES "
                "('Legacy note', 'Preserve this data')"
            )
        )

    monkeypatch.setattr("app.core.settings.settings.DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")

    inspector = inspect(engine)
    with engine.connect() as connection:
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
        preserved_title = connection.execute(
            text("SELECT title FROM notes")
        ).scalar_one()

    assert revision == "20260721_0009"
    assert preserved_title == "Legacy note"
    assert "workflow_runs" in inspector.get_table_names()


def test_migrations_adopt_tables_created_ahead_of_revision(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'hybrid.db'}"
    monkeypatch.setattr("app.core.settings.settings.DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "20260721_0007")

    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    command.upgrade(config, "head")

    with engine.connect() as connection:
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    assert revision == "20260721_0009"
