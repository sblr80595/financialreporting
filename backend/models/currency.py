"""Currency and FX rate models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CurrencyInfo(BaseModel):
    """Currency configuration for an entity."""

    entity_name: str = Field(..., description="Normalized entity name/code")
    default_currency: str = Field(..., description="ISO currency code (e.g., USD, INR)")
    currency_symbol: str = Field(..., description="Currency symbol/prefix")
    currency_name: str = Field(..., description="Human readable currency name")
    decimal_places: int = Field(2, description="Number of decimal places to show")
    format: Optional[str] = Field(
        None, description="Excel-style formatting string if available"
    )


class FxRate(BaseModel):
    """Represents a single FX rate."""

    base_currency: str
    target_currency: str
    rate: float
    as_of: datetime
    source: str


class FxRateResponse(BaseModel):
    """Response shape for FX rate lookups."""

    base_currency: str
    rates: List[FxRate]
    last_refreshed: datetime


class FxConversionResult(BaseModel):
    """Single conversion result."""

    target_currency: str
    converted_amount: float
    rate: float
    as_of: datetime
    source: str


class FxConversionRequest(BaseModel):
    """Request payload for currency conversion."""

    amount: float
    base_currency: str
    target_currencies: List[str]
    as_of: Optional[str] = Field(
        None,
        description="Optional ISO date for SAP historical lookup. Defaults to latest.",
    )


class FxConversionResponse(BaseModel):
    """Response payload for currency conversion."""

    base_currency: str
    amount: float
    conversions: List[FxConversionResult]


class CurrencyContext(BaseModel):
    """Currency context for an entity including FX conversions."""

    entity: str
    local_currency: CurrencyInfo
    reporting_currencies: List[str]
    rates: List[FxRate]
    last_refreshed: datetime
