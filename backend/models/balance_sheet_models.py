"""Balance Sheet data models."""

from typing import Dict, List, Optional

from pydantic import BaseModel


class BSLineItem(BaseModel):
    """
    Single line item in Balance Sheet.

    Attributes:
        particulars: Description of the line item
        note: Note reference number
        amount: Amount value (always positive, no negative signs)
        is_subtotal: Whether this is a subtotal line
        is_total: Whether this is a total line
        indent_level: Indentation level for formatting (0-3)
    """

    particulars: str
    note: Optional[str] = None
    amount: Optional[float] = None
    is_subtotal: bool = False
    is_total: bool = False
    indent_level: int = 0


class BSSection(BaseModel):
    """
    Section of Balance Sheet (Assets, Equity, Liabilities).

    Attributes:
        section_name: Name of the section (e.g., "ASSETS", "EQUITY")
        line_items: List of line items in this section
    """

    section_name: str
    line_items: List[BSLineItem]


class BalanceSheetStatement(BaseModel):
    """
    Complete Balance Sheet Statement.

    Attributes:
        company_name: Name of the company
        as_at_date: Balance sheet date
        sections: List of BS sections
        metadata: Additional metadata about generation
    """

    company_name: str
    as_at_date: str
    sections: List[BSSection]
    metadata: Optional[Dict] = None


class BSGenerationRequest(BaseModel):
    """
    Request to generate Balance Sheet statement.

    Attributes:
        company_name: Name of the company/entity
        as_at_date: Balance sheet date (e.g., "30 June 2025")
        note_numbers: Optional (ignored, uses entity-specific config)
    """

    company_name: str
    as_at_date: str = "30 June 2025"
    note_numbers: Optional[List[str]] = None


class BSGenerationResponse(BaseModel):
    """
    Response from Balance Sheet generation.

    Attributes:
        success: Whether generation was successful
        message: Status message
        statement: Generated Balance Sheet statement (optional)
        output_file: Path to generated Excel file
    """

    success: bool
    message: str
    statement: Optional[BalanceSheetStatement] = None
    output_file: Optional[str] = None