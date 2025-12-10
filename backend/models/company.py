"""Company-related data models."""

from typing import List

from pydantic import BaseModel


class NoteInfo(BaseModel):
    """
    Financial note information model.

    Attributes:
        number: Note number (e.g., "24", "25")
        title: Note title (e.g., "Revenue from Operations")
    """
    number: str
    title: str


class Company(BaseModel):
    """
    Company model with basic information.

    Represents a company entity with its associated financial notes.

    Attributes:
        name: Unique company name/identifier.
        csv_file: Name of the CSV file containing trial balance data.
        notes_count: Total number of financial notes for this company.
        notes: List of note information (number and title) available for this company.
    """

    name: str
    csv_file: str
    notes_count: int
    notes: List[NoteInfo]  # Changed from List[str] to List[NoteInfo]


class NoteCategory(BaseModel):
    """
    Financial note category model.

    Groups notes by financial statement type (P&L, Balance Sheet, etc.).

    Attributes:
        id: Category identifier (e.g., "profit-loss", "balance-sheet").
        name: Human-readable category name.
        description: Detailed description of category purpose.
        notes_count: Number of notes in this category.
        notes: List of note information (number and title) in this category.
    """

    id: str
    name: str
    description: str
    notes_count: int
    notes: List[NoteInfo]  # Changed from List[str] to List[NoteInfo]


class CompanyWithCategories(BaseModel):
    """
    Company model with categorized notes.

    Extended company model that includes notes organized by categories
    for better organization and filtering.

    Attributes:
        name: Company name/identifier.
        csv_file: Trial balance CSV filename.
        notes_count: Total number of notes.
        notes: Complete list of all note information (number and title).
        categories: List of note categories with their respective notes.
    """

    name: str
    csv_file: str
    notes_count: int
    notes: List[NoteInfo]  # Changed from List[str] to List[NoteInfo]
    categories: List[NoteCategory]
