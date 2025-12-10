# ============================================================================
# FILE: backend/routes/bs_finalyzer_routes.py
# ============================================================================
"""BS Finalyzer generation API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.models.balance_sheet_models import BSGenerationResponse
from backend.services.bs_finalyzer_service import BSFinalyzerService
from backend.services.bs_statement_service import BSStatementService  # ADD THIS IMPORT
from backend.services.path_service import PathService

router = APIRouter()


# ADD THIS NEW ENDPOINT
@router.get("/bs-finalyzer-readiness/{company_name}")
async def check_bs_finalyzer_readiness(company_name: str):
    """
    Check if all required notes are available for BS Finalyzer generation.

    Args:
        company_name: Name of the company

    Returns:
        Readiness status with detailed information
    """
    try:
        readiness = BSStatementService.check_bs_readiness(company_name)
        return {
            **readiness,
            "statement_type": "BS_Finalyzer",
            "message": "BS Finalyzer readiness check",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error checking BS Finalyzer readiness: {str(e)}"
        )


@router.post("/generate-bs-finalyzer")
async def generate_bs_finalyzer(
    company_name: str,
    period_label: str = "2025 Mar YTD",
    entity_info: str = "Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual",
    currency: str = "Malaysian Ringgit",
    scenario: str = "Actual",
):
    """
    Generate BS Statement Finalyzer matching exact Excel template.

    Args:
        company_name: Name of the company
        period_label: Period label (e.g., "2025 Mar YTD")
        entity_info: Entity information line
        currency: Currency name
        scenario: Scenario type

    Returns:
        BSGenerationResponse with statement data and file path
    """
    try:
        # ADD READINESS CHECK
        readiness = BSStatementService.check_bs_readiness(company_name)
        
        if not readiness["is_ready"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Cannot generate BS Finalyzer. Not all required notes are available.",
                    "missing_notes": readiness["missing_notes"],
                    "completeness": readiness["completeness_percentage"],
                    "found_notes": readiness["found_notes"],
                },
            )
        
        result = BSFinalyzerService.generate_bs_finalyzer(
            company_name=company_name,
            period_label=period_label,
            entity_info=entity_info,
            currency=currency,
            scenario=scenario,
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating BS Finalyzer: {str(e)}"
        )


@router.get("/download-bs-finalyzer/{company_name}")
async def download_latest_bs_finalyzer(company_name: str):
    """
    Download the most recently generated BS Finalyzer Excel file.

    Args:
        company_name: Name of the company

    Returns:
        Excel file download
    """
    try:
        path_service = PathService(company_name)
        bs_dir = (
            path_service.get_financial_statements_dir(company_name) / "BS_Finalyzer"
        )

        if not bs_dir.exists():
            raise HTTPException(
                status_code=404, detail=f"No BS Finalyzer found for {company_name}"
            )

        # Find the most recent BS Finalyzer file
        bs_files = list(bs_dir.glob("BS_Finalyzer_*.xlsx"))

        if not bs_files:
            raise HTTPException(
                status_code=404, detail=f"No BS Finalyzer found for {company_name}"
            )

        latest_file = max(bs_files, key=lambda p: p.stat().st_mtime)

        return FileResponse(
            path=str(latest_file),
            filename=f"BS_Finalyzer_{company_name}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bs-finalyzer-list/{company_name}")
async def list_bs_finalyzer(company_name: str):
    """
    List all generated BS Finalyzer for a company with metadata.

    Args:
        company_name: Name of the company

    Returns:
        List of generated finalyzers with timestamps and file paths
    """
    try:
        path_service = PathService(company_name)
        bs_dir = (
            path_service.get_financial_statements_dir(company_name) / "BS_Finalyzer"
        )

        if not bs_dir.exists():
            return {"company_name": company_name, "finalyzers": [], "count": 0}

        bs_files = list(bs_dir.glob("BS_Finalyzer_*.xlsx"))

        finalyzers = []
        for file_path in sorted(
            bs_files, key=lambda p: p.stat().st_mtime, reverse=True
        ):
            stat = file_path.stat()
            finalyzers.append(
                {
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "size_bytes": stat.st_size,
                    "generated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "download_url": f"/api/download-bs-finalyzer/{company_name}",
                }
            )

        return {
            "company_name": company_name,
            "finalyzers": finalyzers,
            "count": len(finalyzers),
            "latest": finalyzers[0] if finalyzers else None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))