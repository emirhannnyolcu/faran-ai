from sqlalchemy.orm import Session

from app.models.note import Note


class NoteRepository:
    """Database access for notes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, note: Note) -> Note:
        """Persist a note within the caller-managed transaction."""
        self.db.add(note)
        self.db.flush()
        self.db.refresh(note)
        return note

    def list_all(self) -> list[Note]:
        """Return all stored notes."""
        return self.db.query(Note).all()

    def get_by_id(self, note_id: int) -> Note | None:
        """Return a note by id, if it exists."""
        return self.db.query(Note).filter(Note.id == note_id).first()

    def delete(self, note: Note) -> None:
        """Delete a note within the caller-managed transaction."""
        self.db.delete(note)
        self.db.flush()
