import argparse

from app.core.database import SessionLocal
from app.memory.service import MemoryService
from app.repositories.memory_repository import MemoryRepository


def reindex_memory() -> int:
    """Rebuild all vectors with the configured embedding provider."""
    db = SessionLocal()
    try:
        count = MemoryService(MemoryRepository(db)).reindex_all()
        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    """Run FARAN maintenance commands."""
    parser = argparse.ArgumentParser(description="FARAN maintenance commands")
    parser.add_argument(
        "command",
        choices=["reindex-memory"],
        help="Maintenance command to run",
    )
    args = parser.parse_args()
    if args.command == "reindex-memory":
        count = reindex_memory()
        print(f"Reindexed {count} memory items.")


if __name__ == "__main__":
    main()
