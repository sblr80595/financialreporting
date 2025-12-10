"""PNL Schedule Finalyzer API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.models.financial_statement import PLScheduleGenerationResponse
from backend.services.pnl_schedule_finalyzer_service import PNLScheduleFinalyzerService
from backend.services.pl_statement_service import PLStatementService

router = APIRouter()


@router.post("/generate-pnl-schedule", response_model=PLScheduleGenerationResponse)
async def generate_pnl_schedule(
    company_name: str = Query(..., description="Company name"),
    period_label: str = Query("2025 Mar YTD", description="Period label"),
    entity_info: str = Query(
        "Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual",
        description="Entity information line"
    ),
    currency: str = Query("Malaysian Ringgit", description="Currency name"),
    scenario: str = Query("Actual", description="Scenario type"),
    show_currency_prefix: bool = Query(
        True, 
        description="Show currency prefix (e.g., 'RM 1,234.56' if True, '1,234.56' if False)"
    ),
    currency_prefix: str = Query(
        "RM", 
        description="Currency prefix to use (e.g., 'RM', 'INR', 'USD')"
    ),
    convert_to_lakh: bool = Query(
        False,
        description="Convert values to lakhs by dividing by 100,000 (e.g., 136,138,775 becomes 1,361.39)"
    ),
):
    """
    Generate PNL Schedule Finalyzer with detailed line items from notes.

    This endpoint:
    1. Checks if all required notes are available
    2. Extracts detailed line items from each note markdown file
    3. Parses categories and sub-categories from notes (NO consol codes)
    4. Generates schedule with:
       - Header section (Company, Period, Entity info)
       - Gray metadata section (Entity, Period Id, Currency, Scenario)
       - "PL Schedule" section marker (orange)
       - Individual note sections with line items
       - For Tax (Note 32): Extracts "Current tax" and "Deferred tax" only
    5. Currency formatting options:
       - show_currency_prefix=True: "RM 1,234.56"
       - show_currency_prefix=False: "1,234.56"
    6. Value conversion options:
       - convert_to_lakh=True: Divides by 100,000 (e.g., 136,138,775 → 1,361.39)
       - convert_to_lakh=False: Shows actual values (e.g., 136,138,775.00)
    7. Exports to Excel matching template format
    8. Saves in financial_statements/{company_name}/PNL_Schedule/ directory

    Args:
        company_name: Name of the company
        period_label: Period label (e.g., "2025 Mar YTD")
        entity_info: Entity information line
        currency: Currency name
        scenario: Scenario type
        show_currency_prefix: Show currency prefix (True) or just numbers (False)
        currency_prefix: Currency prefix to use (e.g., "RM", "INR", "USD")
        convert_to_lakh: Convert values to lakhs by dividing by 100,000

    Returns:
        PLScheduleGenerationResponse with file path

    Examples:
        With currency prefix in lakhs:
        POST /api/generate-pnl-schedule?company_name=ABC&show_currency_prefix=true&currency_prefix=RM&convert_to_lakh=true
        Input: 136,138,775 → Output: RM 1,361.39
        
        Without currency prefix, actual values:
        POST /api/generate-pnl-schedule?company_name=ABC&show_currency_prefix=false&convert_to_lakh=false
        Input: 136,138,775 → Output: 136,138,775.00
    """
    # Check readiness first
    readiness = PLStatementService.check_pl_readiness(company_name)

    if not readiness["is_ready"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot generate PNL Schedule. Not all required notes are available.",
                "missing_notes": readiness["missing_notes"],
                "completeness": readiness["completeness_percentage"],
                "found_notes": readiness["found_notes"],
            },
        )

    result = PNLScheduleFinalyzerService.generate_pnl_schedule(
        company_name=company_name,
        period_label=period_label,
        entity_info=entity_info,
        currency=currency,
        scenario=scenario,
        show_currency_prefix=show_currency_prefix,
        currency_prefix=currency_prefix,
        convert_to_lakh=convert_to_lakh,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.get("/download-pnl-schedule/{company_name}")
async def download_latest_pnl_schedule(company_name: str):
    """
    Download the most recently generated PNL Schedule Excel file.

    Args:
        company_name: Name of the company

    Returns:
        Excel file download

    Example:
        GET /api/download-pnl-schedule/Chemopharm_Sdn_Bhd
    """
    from backend.services.path_service import PathService

    path_service = PathService(company_name)
    schedule_dir = (
        path_service.get_financial_statements_dir(company_name) / "PNL_Schedule"
    )

    if not schedule_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No PNL Schedule found for {company_name}",
        )

    # Find the most recent PNL Schedule file
    schedule_files = list(schedule_dir.glob("PNL_Schedule_*.xlsx"))

    if not schedule_files:
        raise HTTPException(
            status_code=404,
            detail=f"No PNL Schedule found for {company_name}",
        )

    latest_file = max(schedule_files, key=lambda p: p.stat().st_mtime)

    return FileResponse(
        path=str(latest_file),
        filename=f"PNL_Schedule_{company_name}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/pnl-schedule-list/{company_name}")
async def list_pnl_schedules(company_name: str):
    """
    List all generated PNL Schedules for a company with metadata.

    Args:
        company_name: Name of the company

    Returns:
        List of generated PNL Schedules with timestamps and file paths

    Example:
        GET /api/pnl-schedule-list/Chemopharm_Sdn_Bhd
    """
    from backend.services.path_service import PathService

    path_service = PathService(company_name)
    schedule_dir = (
        path_service.get_financial_statements_dir(company_name) / "PNL_Schedule"
    )

    if not schedule_dir.exists():
        return {"company_name": company_name, "schedules": [], "count": 0}

    schedule_files = list(schedule_dir.glob("PNL_Schedule_*.xlsx"))

    schedules = []
    for file_path in sorted(schedule_files, key=lambda p: p.stat().st_mtime, reverse=True):
        stat = file_path.stat()
        schedules.append(
            {
                "filename": file_path.name,
                "file_path": str(file_path),
                "size_bytes": stat.st_size,
                "generated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "download_url": f"/api/download-pnl-schedule/{company_name}",
            }
        )

    return {
        "company_name": company_name,
        "schedules": schedules,
        "count": len(schedules),
        "latest": schedules[0] if schedules else None,
    }


@router.get("/pnl-schedule-readiness/{company_name}")
async def check_pnl_schedule_readiness(company_name: str):
    """
    Check if all required notes are available for PNL Schedule generation.

    Args:
        company_name: Name of the company

    Returns:
        Readiness status with detailed information

    Example:
        GET /api/pnl-schedule-readiness/Chemopharm_Sdn_Bhd
    """
    try:
        readiness = PLStatementService.check_pl_readiness(company_name)
        return {
            **readiness,
            "statement_type": "PNL_Schedule",
            "message": "PNL Schedule readiness check",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking PNL Schedule readiness: {str(e)}"
        )