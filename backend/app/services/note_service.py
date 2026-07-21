from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.memory.service import MemoryService
from app.models.note import Note
from app.repositories.memory_repository import MemoryRepository
from app.repositories.note_repository import NoteRepository
from app.services.ai_service import analyze_note


class NoteNotFoundError(Exception):
    """Raised when a note cannot be found."""

    pass


class NotePersistenceError(Exception):
    """Raised when a note cannot be persisted safely."""

    pass


class NoteService:
    """Application service for note use cases."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = NoteRepository(db)
        self.memory_service = MemoryService(MemoryRepository(db))

    def create_note(self, title: str, content: str) -> Note:
        """Analyze and persist a note."""
        analysis = analyze_note(content)
        memory_candidate = self.memory_service.build_candidate(
            title=title,
            content=content,
            analysis=analysis,
        )

        note = Note(
            title=memory_candidate.source_title,
            content=memory_candidate.source_content,
            summary=memory_candidate.summary,
            topic=memory_candidate.topic,
            tags=memory_candidate.tags_text,
            importance=memory_candidate.importance,
            ai_insights=memory_candidate.insights,
        )

        try:
            created_note = self.repository.create(note)
            memory_candidate.source_id = created_note.id
            self.memory_service.persist_candidate(memory_candidate)
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise NotePersistenceError("Note could not be saved") from exc

        return created_note

    def list_notes(self) -> list[Note]:
        """Return all notes."""
        return self.repository.list_all()

    def get_note(self, note_id: int) -> Note:
        """Return a note or raise a domain error."""
        note = self.repository.get_by_id(note_id)
        if note is None:
            raise NoteNotFoundError()
        return note

    def delete_note(self, note_id: int) -> None:
        """Delete a note or raise a domain error."""
        note = self.get_note(note_id)

        try:
            self.repository.delete(note)
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise NotePersistenceError("Note could not be deleted") from exc
