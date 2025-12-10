"""Note generation related data models."""

from typing import List, Optional

from pydantic import BaseModel


class NoteGenerationRequest(BaseModel):
    """
    Single note generation request model.

    Used for requesting generation of a specific financial note.

    Attributes:
        company_name: Name of the company.
        note_number: Number of the note to generate.
    """

    company_name: str
    note_number: str


class BatchGenerationRequest(BaseModel):
    """
    Batch note generation request model.

    Used for requesting generation of multiple notes, optionally filtered by category.

    Attributes:
        company_name: Name of the company.
        category_id: Optional category filter (e.g., "profit-loss").
    """

    company_name: str
    category_id: Optional[str] = None


class GenerationResponse(BaseModel):
    """
    Note generation response model.

    Contains result of note generation operation.

    Attributes:
        success: Whether generation was successful.
        message: Descriptive message about the result.
        note_number: Number of the generated note.
        output_file: Path to the generated output file.
        content: Generated note content (markdown).
    """

    success: bool
    message: str
    note_number: Optional[str] = None
    output_file: Optional[str] = None
    content: Optional[str] = None


class BatchGenerationStatus(BaseModel):
    """
    Batch generation status model.

    Tracks progress of batch note generation operation.

    Attributes:
        status: Current status (pending, running, completed, failed).
        total_notes: Total number of notes to generate.
        completed_notes: Number of notes completed so far.
        current_note: Note number currently being processed.
        results: List of generation results for completed notes.
    """

    status: str
    total_notes: int
    completed_notes: int
    current_note: Optional[str] = None
    results: List[GenerationResponse] = []
