"""Company-related API routes."""

from typing import List

from fastapi import APIRouter, HTTPException
from backend.models.currency import CurrencyInfo

# from backend.models.auth import UserInDB  # Disabled - auth not required
from backend.models.company import Company, CompanyWithCategories
from backend.services.company_service import CompanyService

# from backend.utils.dependencies import get_current_active_user  # Disabled - auth not required

router = APIRouter()


@router.get("/companies", response_model=List[Company])
async def list_companies(
    # current_user: UserInDB = Depends(get_current_active_user),  # Disabled - auth not required
):
    """List all available companies with their notes."""
    return CompanyService.get_all_companies()


@router.get("/companies/{company_name}", response_model=Company)
async def get_company_details(
    company_name: str,
    # current_user: UserInDB = Depends(get_current_active_user),  # Disabled - auth not required
):
    """Get details for a specific company."""
    company = CompanyService.get_company_by_name(company_name)
    if not company:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_name}' not found"
        )
    return company


@router.get(
    "/companies/{company_name}/categories", response_model=CompanyWithCategories
)
async def get_company_categories(
    company_name: str,
    # current_user: UserInDB = Depends(get_current_active_user),  # Disabled - auth not required
):
    """Get company details with notes organized by categories."""
    company = CompanyService.get_company_with_categories(company_name)
    if not company:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_name}' not found"
        )
    return company


@router.get("/companies/{company_name}/currency", response_model=CurrencyInfo)
async def get_company_currency(company_name: str):
    """Get currency information for a specific company/entity."""
    try:
        from backend.services.currency_service import CurrencyService

        return CurrencyService.get_entity_currency(company_name)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading currency information: {str(e)}"
        )
