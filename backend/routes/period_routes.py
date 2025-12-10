"""API routes for period management."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Optional

from backend.config.period_config import period_config
from backend.services.period_discovery_service import period_discovery_service

router = APIRouter()


class SetPeriodRequest(BaseModel):
    """Request model for setting period."""
    period_key: str


class AddPeriodRequest(BaseModel):
    """Request model for adding custom period."""
    period_key: str
    column_name: str


class PeriodResponse(BaseModel):
    """Response model for period information."""
    current_period: Optional[str]
    current_period_column: Optional[str]
    available_periods: Dict[str, str]
    period_display_names: Optional[Dict[str, str]] = None


@router.get("/periods", response_model=PeriodResponse)
async def get_periods(entity: Optional[str] = Query(None, description="Entity code to get periods for")):
    """
    Get current period configuration and available periods.
    If entity is provided, returns periods discovered from that entity's trial balance files.
    
    Args:
        entity: Optional entity code (e.g., 'cpm', 'analisa_resource')
    
    Returns:
        Current period info and all available period mappings
    """
    if entity:
        # Discover periods from entity's trial balance files
        discovered_periods = period_discovery_service.discover_periods_for_entity(entity)
        
        # Sort periods chronologically (most recent first)
        discovered_periods = period_discovery_service.sort_periods(discovered_periods)
        
        # Create display names in MMM-YYYY format
        period_display_names = {
            key: period_discovery_service.get_period_display_name(key)
            for key in discovered_periods.keys()
        }
        
        # If periods were discovered, use them; otherwise fall back to defaults
        available_periods = discovered_periods if discovered_periods else period_config.get_available_periods()
    else:
        # Use default/configured periods
        available_periods = period_config.get_available_periods()
        period_display_names = None
    
    return PeriodResponse(
        current_period=period_config.get_current_period(),
        current_period_column=period_config.get_current_period_column(default=None),
        available_periods=available_periods,
        period_display_names=period_display_names
    )


@router.post("/periods/set")
async def set_period(request: SetPeriodRequest):
    """
    Set the active period for all note generations.
    
    This will override any period_column settings in individual JSON configs.
    
    Args:
        request: SetPeriodRequest with period_key
        
    Returns:
        Success message with selected period
        
    Example:
        POST /api/periods/set
        {
            "period_key": "mar_2025"
        }
    """
    try:
        column_name = period_config.set_period(request.period_key)
        
        return {
            "success": True,
            "message": f"Period set to {request.period_key}",
            "period_key": request.period_key,
            "period_column": column_name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/periods/add")
async def add_custom_period(request: AddPeriodRequest):
    """
    Add a custom period mapping.
    
    This allows adding periods not in the default list.
    
    Args:
        request: AddPeriodRequest with period_key and column_name
        
    Returns:
        Success message
        
    Example:
        POST /api/periods/add
        {
            "period_key": "oct_2025",
            "column_name": "Total Oct'25"
        }
    """
    period_config.add_custom_period(request.period_key, request.column_name)
    
    return {
        "success": True,
        "message": f"Custom period added: {request.period_key}",
        "period_key": request.period_key,
        "period_column": request.column_name
    }


@router.post("/periods/reset")
async def reset_period():
    """
    Reset period configuration.
    
    After reset, individual JSON config period_column will be used,
    or default if not specified.
    
    Returns:
        Success message
    """
    period_config.reset()
    
    return {
        "success": True,
        "message": "Period configuration reset. Using JSON config or defaults."
    }