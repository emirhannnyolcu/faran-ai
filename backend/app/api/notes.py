from fastapi import APIRouter, Depends

from app.api.dependencies import get_note_service
from app.models.note import Note
from app.schemas.note import DeleteNoteResponse, NoteCreate, NoteRead
from app.services.note_service import NoteService


router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post("/", response_model=NoteRead)
def create_note(
    note: NoteCreate,
    service: NoteService = Depends(get_note_service),
) -> Note:
    """Create a note after AI analysis."""
    return service.create_note(title=note.title, content=note.content)


@router.get("/", response_model=list[NoteRead])
def list_notes(service: NoteService = Depends(get_note_service)) -> list[Note]:
    """List all notes."""
    return service.list_notes()


@router.get("/{note_id}", response_model=NoteRead)
def get_note(
    note_id: int,
    service: NoteService = Depends(get_note_service),
) -> Note:
    """Return a note by id."""
    return service.get_note(note_id)


@router.delete("/{note_id}", response_model=DeleteNoteResponse)
def delete_note(
    note_id: int,
    service: NoteService = Depends(get_note_service),
) -> DeleteNoteResponse:
    """Delete a note by id."""
    service.delete_note(note_id)

    return DeleteNoteResponse(message="Note deleted successfully")
