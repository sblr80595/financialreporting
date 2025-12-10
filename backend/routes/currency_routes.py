"""Currency and FX endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.models.currency import (
    CurrencyContext,
    CurrencyInfo,
    FxConversionRequest,
    FxConversionResponse,
    FxRateResponse,
)
from backend.services.currency_service import CurrencyService
from backend.services.fx_rate_service import FxRateService

router = APIRouter()
fx_service = FxRateService()


def _parse_targets(targets: Optional[str]) -> List[str]:
    if not targets:
        return []
    return [t.strip().upper() for t in targets.split(",") if t.strip()]


@router.get("/currency/{entity}", response_model=CurrencyInfo, tags=["Currency"])
async def get_currency(entity: str):
    """Get currency info for an entity (case-insensitive, alias-friendly)."""
    return CurrencyService.get_entity_currency(entity)


@router.get(
    "/currency/context/{entity}",
    response_model=CurrencyContext,
    tags=["Currency"],
)
async def get_currency_context(
    entity: str,
    targets: Optional[str] = Query(
        None,
        description="Comma separated reporting currencies (defaults to USD,INR)",
        example="USD,INR",
    ),
    force_refresh: bool = Query(
        False,
        description="Force refresh FX rates instead of using cached values",
    ),
):
    """Get local currency plus reporting FX context (USD/INR by default)."""
    currency_info = CurrencyService.get_entity_currency(entity)
    target_list = CurrencyService.reporting_targets(
        currency_info.default_currency, preferred=_parse_targets(targets)
    )
    rates = fx_service.get_rates(
        currency_info.default_currency, target_list, force_refresh=force_refresh
    )
    return CurrencyContext(
        entity=currency_info.entity_name,
        local_currency=currency_info,
        reporting_currencies=target_list,
        rates=rates,
        last_refreshed=datetime.utcnow(),
    )


@router.get(
    "/currency/rates",
    response_model=FxRateResponse,
    tags=["Currency"],
)
async def get_rates(
    base_currency: str,
    target_currencies: List[str] = Query(..., description="Target currencies e.g. USD,INR"),
    force_refresh: bool = Query(False, description="Force refresh FX rates"),
):
    """Fetch FX rates for a base currency."""
    if not target_currencies:
        raise HTTPException(status_code=400, detail="target_currencies is required")
    rates = fx_service.get_rates(base_currency, target_currencies, force_refresh=force_refresh)
    if not rates:
        raise HTTPException(status_code=502, detail="Unable to fetch FX rates")
    return FxRateResponse(
        base_currency=base_currency.upper(),
        rates=rates,
        last_refreshed=datetime.utcnow(),
    )


@router.post(
    "/currency/convert",
    response_model=FxConversionResponse,
    tags=["Currency"],
)
async def convert_currency(payload: FxConversionRequest):
    """Convert an amount from base to target currencies."""
    if not payload.target_currencies:
        raise HTTPException(status_code=400, detail="target_currencies cannot be empty")

    conversions = fx_service.convert(payload.amount, payload.base_currency, payload.target_currencies)
    if not conversions:
        raise HTTPException(status_code=502, detail="Unable to convert currency with current FX sources")

    return FxConversionResponse(
        base_currency=payload.base_currency.upper(),
        amount=payload.amount,
        conversions=conversions,
    )
