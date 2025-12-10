# ============================================================================
# FILE: backend/routes/cashflow_finalyzer_routes.py
# ============================================================================
"""Cash Flow Statement Finalyzer API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.services.cashflow_finalyzer_service import CashFlowFinalyzerService
from backend.services.path_service import PathService

router = APIRouter()


@router.post("/generate-cashflow-finalyzer")
async def generate_cashflow_finalyzer(
    company_name: str = Query(..., description="Company name"),
    period_label: str = Query("2025 Mar YTD", description="Period label (e.g., '2025 Mar YTD')"),
    entity_info: str = Query(
        "Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual",
        description="Entity information line"
    ),
    currency: str = Query("Malaysian Ringgit", description="Currency name"),
    scenario: str = Query("Cashflow", description="Scenario type"),
):
    """
    Generate Cash Flow Statement Finalyzer matching exact Excel template.

    This endpoint:
    1. Checks if Cash Flow Statement markdown file exists
    2. Extracts all line items from the markdown
    3. Compiles them into a Cash Flow Finalyzer matching the exact template
    4. Includes:
       - Company header with red text
       - Period label
       - Entity information
       - Yellow "Cashflow" header
       - Gray metadata section (Entity, Period Id, Currency, Scenario)
       - Operating Activities section with:
         * Operating profit before working capital changes
         * Profit before taxes
         * Adjustments (Finance cost, Interest, Depreciation, etc.)
         * Working capital changes
         * Tax paid
       - Investing Activities section
       - Financing Activities section
       - Net increase/decrease in cash
    5. Exports to Excel with exact formatting
    6. Saves in financial_statements/{company_name}/CashFlow_Finalyzer/ directory

    Args:
        company_name: Name of the company
        period_label: Period label (e.g., "2025 Mar YTD")
        entity_info: Entity information line
        currency: Currency name
        scenario: Scenario type

    Returns:
        Response with success status and file path

    Example:
        POST /api/generate-cashflow-finalyzer?company_name=CPM&period_label=2025%20Mar%20YTD
    """
    # Check readiness first
    readiness = CashFlowFinalyzerService.check_cashflow_finalyzer_readiness(company_name)

    if not readiness["is_ready"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": readiness["message"],
                "company_name": company_name,
            },
        )

    result = CashFlowFinalyzerService.generate_cashflow_finalyzer(
        company_name=company_name,
        period_label=period_label,
        entity_info=entity_info,
        currency=currency,
        scenario=scenario,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/download-cashflow-finalyzer/{company_name}")
async def download_latest_cashflow_finalyzer(company_name: str):
    """
    Download the most recently generated Cash Flow Finalyzer Excel file.

    Args:
        company_name: Name of the company

    Returns:
        Excel file download

    Example:
        GET /api/download-cashflow-finalyzer/CPM
    """
    path_service = PathService(company_name)
    cashflow_finalyzer_dir = (
        path_service.get_financial_statements_dir(company_name) / "CashFlow_Finalyzer"
    )

    if not cashflow_finalyzer_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No Cash Flow Finalyzer statements found for {company_name}",
        )

    # Find the most recent Cash Flow Finalyzer file
    cashflow_files = list(cashflow_finalyzer_dir.glob("CashFlow_Finalyzer_*.xlsx"))

    if not cashflow_files:
        raise HTTPException(
            status_code=404,
            detail=f"No Cash Flow Finalyzer statements found for {company_name}",
        )

    latest_file = max(cashflow_files, key=lambda p: p.stat().st_mtime)

    return FileResponse(
        path=str(latest_file),
        filename=f"CashFlow_Finalyzer_{company_name}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/cashflow-finalyzer-list/{company_name}")
async def list_cashflow_finalyzer_statements(company_name: str):
    """
    List all generated Cash Flow Finalyzer statements for a company with metadata.

    Args:
        company_name: Name of the company

    Returns:
        List of generated Cash Flow Finalyzer statements with timestamps and file paths

    Example Response:
    {
        "company_name": "CPM",
        "statements": [
            {
                "filename": "CashFlow_Finalyzer_20250106_143022.xlsx",
                "path": "/path/to/file.xlsx",
                "generated_at": "2025-01-06T14:30:22",
                "size": 25344
            }
        ],
        "count": 1,
        "latest": {...}
    }

    Example:
        GET /api/cashflow-finalyzer-list/CPM
    """
    result = CashFlowFinalyzerService.list_cashflow_finalyzer_statements(company_name)
    return result


@router.get("/cashflow-finalyzer-readiness/{company_name}")
async def check_cashflow_finalyzer_readiness(company_name: str):
    """
    Check if Cash Flow Statement markdown is available for Finalyzer generation.

    This checks if the Note_CASHFLOW_*.md file exists for the company.

    Args:
        company_name: Name of the company

    Returns:
        Readiness status with detailed information

    Example Response:
    {
        "company_name": "CPM",
        "is_ready": true,
        "markdown_file": "/path/to/Note_CASHFLOW_Cash_Flow_Statement.md",
        "message": "Cash Flow Statement markdown file found. Ready to generate Finalyzer."
    }

    Example:
        GET /api/cashflow-finalyzer-readiness/CPM
    """
    try:
        readiness = CashFlowFinalyzerService.check_cashflow_finalyzer_readiness(company_name)
        return {
            **readiness,
            "statement_type": "CashFlow_Finalyzer",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error checking Cash Flow Finalyzer readiness: {str(e)}"
        )


@router.delete("/cashflow-finalyzer/{company_name}/{filename}")
async def delete_cashflow_finalyzer(company_name: str, filename: str):
    """
    Delete a specific Cash Flow Finalyzer file.

    Args:
        company_name: Name of the company
        filename: Name of the file to delete

    Returns:
        Success message

    Example:
        DELETE /api/cashflow-finalyzer/CPM/CashFlow_Finalyzer_20250106_143022.xlsx
    """
    try:
        path_service = PathService(company_name)
        cashflow_finalyzer_dir = (
            path_service.get_financial_statements_dir(company_name) / "CashFlow_Finalyzer"
        )
        
        file_path = cashflow_finalyzer_dir / filename

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Cash Flow Finalyzer file not found: {filename}"
            )

        # Delete the file
        file_path.unlink()

        return {
            "success": True,
            "message": f"Successfully deleted {filename}",
            "company_name": company_name,
            "deleted_file": filename
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting Cash Flow Finalyzer: {str(e)}"
        )