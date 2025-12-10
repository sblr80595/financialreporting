# ============================================================================
# FILE: backend/routes/equity_finalyzer_routes.py
# ============================================================================
"""Equity Schedule Finalyzer generation API routes."""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path


from backend.models.bs_schedule_finalyzer import BSScheduleGenerationResponse
from backend.services.equity_finalyzer_service import EquityFinalyzerService
from backend.services.bs_statement_service import BSStatementService
from backend.services.path_service import PathService

router = APIRouter()


# Request Model (Unchanged)
class EquityScheduleRequest(BaseModel):
    company_name: str
    period_label: str = "2025 Mar YTD"
    entity_info: str = "Entity: CPM Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual"
    currency: str = "Malaysian Ringgit"
    scenario: str = "Actual"
    show_currency_prefix: bool = True
    currency_prefix: str = "RM"
    convert_to_lakh: bool = False


@router.get("/equity-schedule-readiness/{company_name}")
async def check_equity_schedule_readiness(company_name: str):
    """
    Check if all required notes are available for Equity Schedule generation.
    
    Primary requirements (is_ready=True): Note 14 and Note 15 Markdown files must be found.
    Secondary requirement (optional): SOCIE.md is checked but does not block generation.

    Args:
        company_name: Name of the company

    Returns:
        Readiness status with detailed information
    """
    try:
        path_service = PathService(company_name)

        notes_dir = path_service.get_generated_notes_dir()
        
        # --- Define Requirements using only Note Numbers for robust globbing ---
        REQUIRED_NOTES = ["14", "15"]
        OPTIONAL_NOTE = "SOCIE"
        
        found_notes = []
        
        if not notes_dir.exists():
            return {
                "company_name": company_name,
                "is_ready": False,
                "found_notes": [],
                "missing_notes": REQUIRED_NOTES + [OPTIONAL_NOTE],
                "total_required": len(REQUIRED_NOTES) + 1,
                "total_found": 0,
                "completeness_percentage": 0.00,
                "statement_type": "Equity_Schedule",
                "message": f"Generated notes directory not found for {company_name}",
            }
        
        # 1. Check Primary Requirements (Note 14 and 15) using glob
        for note_number in REQUIRED_NOTES:
            # Check for ANY file starting with 'Note_{number}_' and ending in '.md'
            if list(notes_dir.glob(f"Note_{note_number}*.md")): 
                found_notes.append(note_number)
        
        # 2. Check Secondary Requirement (SOCIE)
        socie_is_missing = True
        if list(notes_dir.glob(f"*{OPTIONAL_NOTE}*.md")):
            found_notes.append(OPTIONAL_NOTE)
            socie_is_missing = False

        # --- Determine Readiness Status ---
        all_required_set = set(REQUIRED_NOTES)
        found_required_set = set(found_notes) & all_required_set
        

        # FIX 1: Pass company_name for robust path generation
        notes_dir = path_service.get_generated_notes_dir(company_name)
        
        # --- Define Requirements ---
        REQUIRED_NOTES = ["14", "15"]
        OPTIONAL_NOTE = "SOCIE"
        
        found_notes = []
        socie_found = False
        socie_file_path = None

        if not notes_dir.exists():
            return {
                "company_name": company_name,
                "is_ready": False,
                "found_notes": [],
                "missing_notes": REQUIRED_NOTES + [OPTIONAL_NOTE],
                "total_required": len(REQUIRED_NOTES) + 1,
                "total_found": 0,
                "completeness_percentage": 0.00,
                "statement_type": "Equity_Schedule",
                "message": f"Generated notes directory not found for {company_name}",
            }
        
        # 1. Check Primary Requirements (Note 14 and 15) using robust glob
        for note_number in REQUIRED_NOTES:
            # Check for ANY file starting with 'Note_{number}_' and ending in '.md'
            if list(notes_dir.glob(f"Note_{note_number}*.md")): 
                found_notes.append(note_number)
        
        # 2. Check Secondary Requirement (SOCIE)
        socie_files = list(notes_dir.glob(f"*{OPTIONAL_NOTE}*.md"))
        if socie_files:
            socie_found = True
            socie_file_path = str(socie_files[0])
            found_notes.append(OPTIONAL_NOTE)

        # --- Determine Readiness Status (FIX 2: SOCIE is OPTIONAL) ---
        all_required_set = set(REQUIRED_NOTES)
        found_required_set = set(found_notes) & all_required_set
        

        equity_missing = sorted(list(all_required_set - found_required_set))
        
        # is_ready requires *only* Note 14 and 15 to be found.
        is_ready = len(equity_missing) == 0
       
        # --- Prepare Output ---
        all_equity_notes = REQUIRED_NOTES + [OPTIONAL_NOTE]
        total_required = len(all_equity_notes) 
        total_found = len(set(found_notes))
        completeness = (total_found / total_required * 100) if total_required > 0 else 0
        
        missing_notes_output = equity_missing + ([OPTIONAL_NOTE] if socie_is_missing else [])
        
        if is_ready:
            message = "Equity Schedule is ready for generation."
            if socie_is_missing:
                 message += " (Note: SOCIE file is missing but generation will proceed.)"
        else:
            message = f"Cannot proceed. Missing REQUIRED notes: {', '.join(equity_missing)}"

        
        # --- Prepare Output ---
        total_required_all = len(REQUIRED_NOTES) + 1
        total_found_all = len(set(found_notes))
        completeness = (total_found_all / total_required_all * 100) if total_required_all > 0 else 0
        
        missing_notes_output = equity_missing + ([OPTIONAL_NOTE] if not socie_found else [])
        
        # FIX 3: Custom message as requested
        if is_ready:
            message = "Equity Schedule is ready for generation."
            if not socie_found:
                 # Display message telling SOCIE to be generated
                 message += " Please generate SOCIE to include full movement details."
        else:
            message = f"❌ Missing required notes: {', '.join(equity_missing)}"


        return {
            "company_name": company_name,
            "is_ready": is_ready,
            "found_notes": sorted(list(set(found_notes))),
            "missing_notes": missing_notes_output,

            "total_required": total_required,
            "total_found": total_found,

            "required_notes": REQUIRED_NOTES,
            "optional_notes": {
                 "SOCIE": {
                    "found": socie_found,
                    "file_path": socie_file_path,
                    "description": "Statement of Changes in Equity (optional)"
                 }
            },
            "total_required": total_required_all,
            "total_found": total_found_all,

            "completeness_percentage": round(completeness, 2),
            "statement_type": "Equity_Schedule",
            "message": message,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"CRASH: Error checking Equity Schedule readiness due to path failure: {str(e)}"
        )


@router.post("/v1/equity-schedule/generate", response_model=BSScheduleGenerationResponse)
async def generate_equity_schedule(request: EquityScheduleRequest):
    """
    Generate the detailed Equity Schedule Finalyzer in Excel format.
    
    Generation proceeds if Notes 14 and 15 are found. Missing SOCIE is handled internally by the service.


    Args:
        request: EquityScheduleRequest with all parameters

    Returns:
        BSScheduleGenerationResponse with file path and metadata
    """
    try:
        # RESOLUTION: Correctly AWAIT the asynchronous readiness check function.
        readiness = await check_equity_schedule_readiness(request.company_name)
        
        # Stop if the mandatory notes (14 and 15) are missing.
        if not readiness["is_ready"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Cannot generate Equity Schedule. Not all REQUIRED notes (14, 15) are available.",
                    "message": readiness["message"], # Use the detailed message from readiness check
                    "missing_notes": readiness["missing_notes"],
                    "completeness": readiness["completeness_percentage"],
                    "found_notes": readiness["found_notes"],
                },
            )
        
        # Generation proceeds because is_ready is True (14 & 15 present).
        result = EquityFinalyzerService.generate_bs_schedule(
            company_name=request.company_name,
            period_label=request.period_label,
            entity_info=request.entity_info,
            currency=request.currency,
            scenario=request.scenario,
            show_currency_prefix=request.show_currency_prefix,
            currency_prefix=request.currency_prefix,
            convert_to_lakh=request.convert_to_lakh,
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating Equity Schedule: {str(e)}"
        )


# ----------------------------------------------------------------------------
# --- Download and List Endpoints (Unchanged) ---
# ----------------------------------------------------------------------------
@router.get("/download-equity-schedule/{company_name}")
async def download_latest_equity_schedule(company_name: str):
    """Download the most recently generated Equity Schedule Excel file."""
    try:
        path_service = PathService(company_name)
        schedule_dir = (
            path_service.get_financial_statements_dir(company_name) / "Equity_Schedule"
        )

        if not schedule_dir.exists():
            raise HTTPException(status_code=404, detail=f"No Equity Schedule found for {company_name}")

        schedule_files = list(schedule_dir.glob("Equity_Schedule_*.xlsx"))

        if not schedule_files:
            raise HTTPException(status_code=404, detail=f"No Equity Schedule found for {company_name}")

        latest_file = max(schedule_files, key=lambda p: p.stat().st_mtime)

        return FileResponse(
            path=str(latest_file),
            filename=f"Equity_Schedule_{company_name}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------
# --- List Endpoint ---
# ----------------------------------------------------------------------------
@router.get("/equity-schedule-list/{company_name}")
async def list_equity_schedules(company_name: str):
    """List all generated Equity Schedules for a company with metadata."""
    try:
        path_service = PathService(company_name)
        schedule_dir = (
            path_service.get_financial_statements_dir(company_name) / "Equity_Schedule"
        )

        if not schedule_dir.exists():
            return {"company_name": company_name, "schedules": [], "count": 0}

        schedule_files = list(schedule_dir.glob("Equity_Schedule_*.xlsx"))

        schedules = []
        for file_path in sorted(
            schedule_files, key=lambda p: p.stat().st_mtime, reverse=True
        ):
            stat = file_path.stat()
            schedules.append(
                {
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "size_bytes": stat.st_size,
                    "generated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "download_url": f"/api/download-equity-schedule/{company_name}",
                }
            )

        return {
            "company_name": company_name,
            "schedules": schedules,
            "count": len(schedules),
            "latest": schedules[0] if schedules else None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))