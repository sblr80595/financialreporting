"""PNL Statement Finalyzer API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.models.financial_statement import (
    PLGenerationRequest,
    PLGenerationResponse,
)
from backend.services.pnl_finalyzer_service import PNLFinalyzerService
from backend.services.pl_statement_service import PLStatementService

router = APIRouter()


@router.post("/generate-pnl-finalyzer", response_model=PLGenerationResponse)
async def generate_pnl_finalyzer(
    company_name: str = Query(..., description="Company name"),
    period_label: str = Query("2025 Mar YTD", description="Period label (e.g., '2025 Mar YTD')"),
    entity_info: str = Query(
        "Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual",
        description="Entity information line"
    ),
    currency: str = Query("Malaysian Ringgit", description="Currency name"),
    scenario: str = Query("Actual", description="Scenario type"),
):
    """
    Generate PNL Statement Finalyzer matching exact Excel template.

    This endpoint:
    1. Checks if all required notes are available
    2. Extracts total amounts from each note markdown file
    3. Compiles them into a PNL statement matching the exact template
    4. Includes:
       - Company header with red text
       - Period label
       - Entity information
       - Yellow PL header
       - Gray metadata section (Entity, Period Id, Currency, Scenario)
       - Income section (Revenue, Other income)
       - Expenses section with Cost of Material Consumed subsection
       - Profit before tax (with orange text)
       - Tax expenses (Current tax, Deferred tax) - NO consol codes
       - Net profit (with orange text)
       - Total comprehensive income (with orange text)
    5. Exports to Excel with exact formatting
    6. Saves in financial_statements/{company_name}/PNL_Finalyzer/ directory

    Args:
        company_name: Name of the company
        period_label: Period label (e.g., "2025 Mar YTD")
        entity_info: Entity information line
        currency: Currency name
        scenario: Scenario type

    Returns:
        PLGenerationResponse with statement data and file path

    Example:
        POST /api/generate-pnl-finalyzer?company_name=Chemopharm%20Sdn.%20Bhd.&period_label=2025%20Mar%20YTD
    """
    # Check readiness first
    readiness = PLStatementService.check_pl_readiness(company_name)

    if not readiness["is_ready"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot generate PNL Finalyzer. Not all required notes are available.",
                "missing_notes": readiness["missing_notes"],
                "completeness": readiness["completeness_percentage"],
                "found_notes": readiness["found_notes"],
            },
        )

    result = PNLFinalyzerService.generate_pnl_finalyzer(
        company_name=company_name,
        period_label=period_label,
        entity_info=entity_info,
        currency=currency,
        scenario=scenario,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.get("/download-pnl-finalyzer/{company_name}")
async def download_latest_pnl_finalyzer(company_name: str):
    """
    Download the most recently generated PNL Finalyzer Excel file.

    Args:
        company_name: Name of the company

    Returns:
        Excel file download

    Example:
        GET /api/download-pnl-finalyzer/ABC_Corp
    """
    from backend.services.path_service import PathService

    path_service = PathService(company_name)
    pnl_finalyzer_dir = (
        path_service.get_financial_statements_dir(company_name) / "PNL_Finalyzer"
    )

    if not pnl_finalyzer_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No PNL Finalyzer statements found for {company_name}",
        )

    # Find the most recent PNL Finalyzer file
    pnl_files = list(pnl_finalyzer_dir.glob("PNL_Finalyzer_*.xlsx"))

    if not pnl_files:
        raise HTTPException(
            status_code=404,
            detail=f"No PNL Finalyzer statements found for {company_name}",
        )

    latest_file = max(pnl_files, key=lambda p: p.stat().st_mtime)

    return FileResponse(
        path=str(latest_file),
        filename=f"PNL_Finalyzer_{company_name}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/pnl-finalyzer-list/{company_name}")
async def list_pnl_finalyzer_statements(company_name: str):
    """
    List all generated PNL Finalyzer statements for a company with metadata.

    Args:
        company_name: Name of the company

    Returns:
        List of generated PNL Finalyzer statements with timestamps and file paths

    Example:
        GET /api/pnl-finalyzer-list/ABC_Corp
    """
    from backend.services.path_service import PathService

    path_service = PathService(company_name)
    pnl_finalyzer_dir = (
        path_service.get_financial_statements_dir(company_name) / "PNL_Finalyzer"
    )

    if not pnl_finalyzer_dir.exists():
        return {"company_name": company_name, "statements": [], "count": 0}

    pnl_files = list(pnl_finalyzer_dir.glob("PNL_Finalyzer_*.xlsx"))

    statements = []
    for file_path in sorted(pnl_files, key=lambda p: p.stat().st_mtime, reverse=True):
        stat = file_path.stat()
        statements.append(
            {
                "filename": file_path.name,
                "file_path": str(file_path),
                "size_bytes": stat.st_size,
                "generated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "download_url": f"/api/download-pnl-finalyzer/{company_name}",
            }
        )

    return {
        "company_name": company_name,
        "statements": statements,
        "count": len(statements),
        "latest": statements[0] if statements else None,
    }


@router.get("/pnl-finalyzer-readiness/{company_name}")
async def check_pnl_finalyzer_readiness(company_name: str):
    """
    Check if all required notes are available for PNL Finalyzer generation.

    This uses the same readiness check as the regular P&L statement.

    Args:
        company_name: Name of the company

    Returns:
        Readiness status with detailed information

    Example:
        GET /api/pnl-finalyzer-readiness/ABC_Corp
    """
    try:
        readiness = PLStatementService.check_pl_readiness(company_name)
        return {
            **readiness,
            "statement_type": "PNL_Finalyzer",
            "message": "PNL Finalyzer readiness check",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking PNL Finalyzer readiness: {str(e)}"
        )