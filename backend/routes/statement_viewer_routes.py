"""
API routes for the Statement Viewer feature.
Provides read-only access to generated statement data.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from backend.services.statement_data_service import StatementDataService

router = APIRouter()


@router.get("/statement-data/{statement_type}/{company_name}")
async def get_statement_data(
    statement_type: str, company_name: str
) -> Dict[str, Any]:
    """
    Get statement data for viewer from latest generated Excel file.

    Args:
        statement_type: Type of statement ('pl', 'bs', 'cf')
        company_name: Name of the company

    Returns:
        {
            "success": true,
            "data": {
                "row_id": {"current": 1000000, "previous": null},
                ...
            },
            "metadata": {
                "company_name": "...",
                "statement_type": "...",
                "has_data": true
            }
        }

    Raises:
        400: Invalid statement type
        404: No generated statement found
        500: Error reading statement
    """
    # Validate statement type
    valid_types = ["pl", "bs", "cf"]
    if statement_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid statement type. Must be one of: {', '.join(valid_types)}",
        )

    try:
        # Extract data based on type
        data = None
        if statement_type == "pl":
            data = StatementDataService.get_pl_statement_data(company_name)
        elif statement_type == "bs":
            data = StatementDataService.get_bs_statement_data(company_name)
        elif statement_type == "cf":
            data = StatementDataService.get_cf_statement_data(company_name)

        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No generated {statement_type.upper()} statement found for {company_name}",
            )

        return {
            "success": True,
            "data": data,
            "metadata": {
                "company_name": company_name,
                "statement_type": statement_type,
                "has_data": len(data) > 0,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading statement data: {str(e)}"
        )


@router.get("/statement-availability/{company_name}")
async def check_statement_availability(company_name: str) -> Dict[str, Any]:
    """
    Check which statements are available for a company.

    Args:
        company_name: Name of the company

    Returns:
        {
            "company_name": "...",
            "available_statements": {
                "pl": true,
                "bs": false,
                "cf": true
            }
        }
    """
    try:
        pl_data = StatementDataService.get_pl_statement_data(company_name)
        bs_data = StatementDataService.get_bs_statement_data(company_name)
        cf_data = StatementDataService.get_cf_statement_data(company_name)

        return {
            "company_name": company_name,
            "available_statements": {
                "pl": pl_data is not None,
                "bs": bs_data is not None,
                "cf": cf_data is not None,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking availability: {str(e)}"
        )
