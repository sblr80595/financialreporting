# ============================================================================
# FILE: backend/models/bs_schedule_finalyzer_models.py
# ============================================================================
"""Balance Sheet Schedule Finalyzer data models."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# NOTE: Importing the core Balance Sheet models from the main model file
# These core definitions MUST exist in backend/models/balance_sheet_models.py
from .balance_sheet_models import BalanceSheetStatement 


class BSScheduleGenerationRequest(BaseModel):
    """
    Request to generate the detailed Balance Sheet Schedule Finalyzer.
    """
    company_name: str = Field(..., description="Name of the company/entity")
    period_label: str = Field("2025 Mar YTD", description="Fiscal period label (e.g., '2025 Mar YTD')")
    entity_info: str = Field("Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual", description="Entity configuration details")
    currency: str = Field("Malaysian Ringgit", description="Currency name")
    scenario: str = Field("Actual", description="Scenario type")
    
    # Arguments used by the service to control output format
    show_currency_prefix: bool = Field(True, description="Whether to include currency prefix in output amounts.")
    currency_prefix: str = Field("RM", description="Currency symbol/prefix to use (e.g., 'RM', '₹').")
    convert_to_lakh: bool = Field(False, description="If True, amounts are divided by 100,000 for Lakhs conversion.")


class BSScheduleGenerationResponse(BaseModel):
    """
    Response model for BS Schedule Finalyzer generation.
    """
    success: bool = Field(..., description="Whether generation was successful")
    message: str = Field(..., description="Status message")
    output_file: Optional[str] = Field(None, description="Path to generated Excel file")
    metadata: Optional[Dict] = Field(None, description="Additional metadata about generation and included periods")

    class Config:
        # Example provided for API documentation (Swagger/Redoc)
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "BS Schedule generated successfully",
                "output_file": "/data/CPM/financial_statements/BS_Schedule/BS_Schedule_20250104_120000.xlsx",
                "metadata": {
                    "generated_at": "2025-01-04T12:00:00",
                    "notes_included": ["3", "4", "5", "6", "7", "8", "10", "11", "12", "13", "14", "15", "17", "18", "19", "20", "21", "22", "23"],
                    "type": "BS_Schedule",
                },
            }
        }