# ============================================================================
# FILE: backend/models/cashflow_models.py
# ============================================================================
"""Cash Flow Statement data models."""

from typing import Optional

from pydantic import BaseModel, Field


class CashFlowGenerationRequest(BaseModel):
    """
    Request to generate Cash Flow Statement Excel template.

    Attributes:
        company_name: Name of the company/entity
        period_ended: Optional period ending date (extracted from markdown if not provided)
    """

    company_name: str = Field(
        ...,
        description="Name of the company/entity",
        example="Chemopharm Sdn. Bhd."
    )
    period_ended: Optional[str] = Field(
        None,
        description="Period ending date (e.g., 'Total Mar'25')",
        example="Total Mar'25"
    )


class CashFlowGenerationResponse(BaseModel):
    """
    Response from Cash Flow Statement generation.

    Attributes:
        success: Whether generation was successful
        message: Status message
        output_file: Path to generated Excel file
        company_name: Name of the company
        period_ended: Period ending date
        source_markdown: Path to source markdown file
    """

    success: bool = Field(
        ...,
        description="Whether the generation was successful"
    )
    message: str = Field(
        ...,
        description="Status message or error details"
    )
    output_file: Optional[str] = Field(
        None,
        description="Path to the generated Excel file"
    )
    company_name: Optional[str] = Field(
        None,
        description="Name of the company"
    )
    period_ended: Optional[str] = Field(
        None,
        description="Period ending date"
    )
    source_markdown: Optional[str] = Field(
        None,
        description="Path to the source markdown file"
    )


class CashFlowReadinessResponse(BaseModel):
    """
    Response for Cash Flow readiness check.

    Attributes:
        company_name: Name of the company
        is_ready: Whether markdown file exists
        markdown_file: Path to markdown file
        period: Period information from the file
        generated_at: When the markdown was created
        file_size: Size of the markdown file
        message: Status message
        error: Error message if any
    """

    company_name: str
    is_ready: bool
    markdown_file: Optional[str] = None
    period: Optional[str] = None
    generated_at: Optional[str] = None
    file_size: Optional[int] = None
    message: str
    error: Optional[str] = None


class CashFlowStatementListResponse(BaseModel):
    """
    Response for listing Cash Flow statements.

    Attributes:
        company_name: Name of the company
        statements: List of statement file details
        count: Number of statements found
        error: Error message if any
    """

    company_name: str
    statements: list
    count: int
    error: Optional[str] = None