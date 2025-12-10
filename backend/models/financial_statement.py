"""Financial statement data models."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class PLLineItem(BaseModel):
    """
    Single line item in P&L statement.

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


class PLSection(BaseModel):
    """
    Section of P&L statement (Income, Expenses, etc.).

    Attributes:
        section_name: Name of the section (e.g., "I. Income")
        line_items: List of line items in this section
    """

    section_name: str
    line_items: List[PLLineItem]


class ProfitLossStatement(BaseModel):
    """
    Complete Profit & Loss Statement.

    Attributes:
        company_name: Name of the company
        period_ended: Period ending date
        sections: List of P&L sections
        metadata: Additional metadata about generation
    """

    company_name: str
    period_ended: str
    sections: List[PLSection]
    metadata: Optional[Dict] = None


class PLGenerationRequest(BaseModel):
    """
    Request to generate P&L statement.

    Attributes:
        company_name: Name of the company/entity
        period_ended: Period ending date (e.g., "30 June 2025")
        note_numbers: Optional (ignored, uses entity-specific config)
    """

    company_name: str
    period_ended: str = "30 June 2025"
    note_numbers: Optional[List[str]] = None


class PLGenerationResponse(BaseModel):
    """
    Response from P&L generation.

    Attributes:
        success: Whether generation was successful
        message: Status message
        statement: Generated P&L statement (optional)
        output_file: Path to generated Excel file
        html_preview: Not used (removed HTML generation)
    """

    success: bool
    message: str
    statement: Optional[ProfitLossStatement] = None
    output_file: Optional[str] = None
    html_preview: Optional[str] = None  # Deprecated, not used


class PNLFinalyzerRequest(BaseModel):
    """Request model for PNL Finalyzer generation."""

    company_name: str = Field(..., description="Name of the company")
    period_ended: str = Field(
        ..., description="Period ending date (e.g., '31st March, 2025')"
    )
    year_label: str = Field(
        default="FY 2024-25", description="Fiscal year label (e.g., 'FY 2024-25')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "ABC Corporation",
                "period_ended": "31st March, 2025",
                "year_label": "FY 2024-25",
            }
        }


class PNLFinalyzerResponse(BaseModel):
    """Response model for PNL Finalyzer generation."""

    success: bool = Field(..., description="Whether generation was successful")
    message: str = Field(..., description="Status message")
    statement: Optional[ProfitLossStatement] = Field(
        None, description="Generated statement data"
    )
    output_file: Optional[str] = Field(None, description="Path to generated Excel file")
    metadata: Optional[dict] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "PNL Finalyzer generated successfully",
                "output_file": "/data/ABC_Corp/financial_statements/PNL_Finalyzer/PNL_Finalyzer_20250104_120000.xlsx",
                "metadata": {
                    "generated_at": "2025-01-04T12:00:00",
                    "notes_used": ["24", "25", "26", "27", "28", "29", "30", "31", "32"],
                    "type": "PNL_Finalyzer",
                },
            }
        }


class PLScheduleGenerationResponse(BaseModel):
    """Response model for PNL Schedule generation."""

    success: bool = Field(..., description="Whether generation was successful")
    message: str = Field(..., description="Status message")
    output_file: Optional[str] = Field(None, description="Path to generated Excel file")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata including notes details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "PNL Schedule generated successfully for Chemopharm Sdn. Bhd.",
                "output_file": "/data/Chemopharm/financial_statements/PNL_Schedule/PNL_Schedule_20250104_120000.xlsx",
                "metadata": {
                    "generated_at": "2025-01-04T12:00:00",
                    "notes_included": ["24", "25", "26", "27", "28", "29", "30", "31", "32"],
                    "type": "PNL_Schedule",
                },
            }
        }

