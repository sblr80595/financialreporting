"""Equity Statement data models."""

from typing import Dict, Optional

from pydantic import BaseModel


class EquityGenerationResponse(BaseModel):
    """Response from Equity Statement generation."""

    success: bool
    message: str
    output_file: Optional[str] = None
    metadata: Optional[Dict] = None