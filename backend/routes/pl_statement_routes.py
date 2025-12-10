# ============================================================================
# FILE: backend/routes/pl_statement_routes.py
# ============================================================================
"""Profit & Loss Statement generation API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.config.settings import settings
from backend.models.financial_statement import (
    PLGenerationRequest,
    PLGenerationResponse,
)
from backend.services.pl_statement_service import PLStatementService
from pathlib import Path
import os

router = APIRouter()


@router.get("/pl-statement-readiness/{company_name}")
async def check_pl_readiness(company_name: str):
    """
    Check if all required notes are available for P&L statement generation.

    This endpoint checks if the entity has generated all required notes:
    - Income notes (24, 25)
    - Expense notes (26, 27, 28, 29, 30, 31)
    - Tax notes (32 or entity-specific)

    Returns:
        - is_ready: True if all notes are available
        - found_notes: List of available notes
        - missing_notes: List of missing notes
        - note_details: Details of each found note with amounts
        - completeness_percentage: Percentage of completed notes

    Args:
        company_name: Name of the company/entity

    Returns:
        Readiness status with detailed information
    """
    try:
        readiness = PLStatementService.check_pl_readiness(company_name)
        return readiness
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking P&L readiness: {str(e)}"
        )


@router.post("/generate-pl-statement", response_model=PLGenerationResponse)
async def generate_pl_statement(request: PLGenerationRequest):
    """
    Generate Profit & Loss statement from generated notes.

    This endpoint:
    1. Checks if all required notes are available
    2. Extracts total amounts from each note markdown file
    3. Compiles them into a complete P&L statement
    4. Applies formulas (Income - Expenses - Tax = Net Profit)
    5. Exports to Excel format with proper formatting
    6. Saves in reports/{company_name}/ directory

    All amounts are displayed as positive values (no negative signs).

    Args:
        request: PLGenerationRequest with company name and period

    Returns:
        PLGenerationResponse with statement data and file path
    """
    # First check if ready
    readiness = PLStatementService.check_pl_readiness(request.company_name)

    if not readiness["is_ready"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot generate P&L statement. Not all required notes are available.",
                "missing_notes": readiness["missing_notes"],
                "completeness": readiness["completeness_percentage"],
            },
        )

    result = PLStatementService.generate_pl_statement(
        company_name=request.company_name,
        period_ended=request.period_ended,
        note_numbers=request.note_numbers,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.get("/download-pl-statement/{company_name}")
async def download_latest_pl_statement(company_name: str):
    """
    Download the most recently generated P&L statement Excel file.

    Args:
        company_name: Name of the company

    Returns:
        Excel file download
    """
    from backend.services.path_service import PathService
    path_service = PathService(company_name)
    reports_dir = path_service.get_financial_statements_dir(company_name) / "PL"

    if not reports_dir.exists():
        raise HTTPException(
            status_code=404, detail=f"No P&L statements found for {company_name}"
        )

    # Find the most recent P&L statement file
    pl_files = list(reports_dir.glob("PL_Statement_*.xlsx"))

    if not pl_files:
        raise HTTPException(
            status_code=404, detail=f"No P&L statements found for {company_name}"
        )

    latest_file = max(pl_files, key=lambda p: p.stat().st_mtime)

    return FileResponse(
        path=str(latest_file),
        filename=f"PL_Statement_{company_name}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/pl-statements-list/{company_name}")
async def list_pl_statements(company_name: str):
    """
    List all generated P&L statements for a company with metadata.

    Args:
        company_name: Name of the company

    Returns:
        List of generated statements with timestamps and file paths
    """
    from backend.services.path_service import PathService
    path_service = PathService(company_name)
    reports_dir = path_service.get_financial_statements_dir(company_name) / "PL"

    if not reports_dir.exists():
        return {"company_name": company_name, "files": [], "statements": [], "count": 0}

    pl_files = list(reports_dir.glob("PL_Statement_*.xlsx"))

    statements = []
    for file_path in sorted(pl_files, key=lambda p: p.stat().st_mtime, reverse=True):
        stat = file_path.stat()
        statements.append({"filename": file_path.name,
                           "file_path": str(file_path),
                           "size_bytes": stat.st_size,
                           "generated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                           "download_url": f"/api/download-pl-statement/{company_name}?filename={file_path.name}",
                           })

    return {
        "company_name": company_name,
        "files": statements,  # For consistency with other endpoints
        "statements": statements,  # For backwards compatibility
        "count": len(statements),
        "latest": statements[0] if statements else None,
    }


@router.get("/pl-statement/{company_name}/download/{filename}")
async def download_pl_statement_file(company_name: str, filename: str):
    """
    Download a specific P&L statement file.

    Args:
        company_name: Name of the company
        filename: Name of the file to download

    Returns:
        File response
    """
    from backend.services.path_service import PathService
    
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=400, 
            detail="Invalid filename"
        )
    
    path_service = PathService(company_name)
    reports_dir = path_service.get_financial_statements_dir(company_name) / "PL"
    file_path = reports_dir / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"File {filename} not found"
        )

    # Verify the file is actually in the expected directory
    if not file_path.is_relative_to(reports_dir):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file path"
        )

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.delete("/pl-statement/{company_name}/{filename}")
async def delete_pl_statement(company_name: str, filename: str):
    """
    Delete a specific P&L statement file.

    Args:
        company_name: Name of the company
        filename: Name of the file to delete

    Returns:
        Success message
    """
    from backend.services.path_service import PathService
    
    print(f"[PL Delete] Attempting to delete: {filename} for company: {company_name}")
    
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        print(f"[PL Delete] Invalid filename detected: {filename}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid filename"
        )
    
    path_service = PathService(company_name)
    reports_dir = path_service.get_financial_statements_dir(company_name) / "PL"
    file_path = reports_dir / filename
    
    print(f"[PL Delete] Looking for file at: {file_path}")

    if not file_path.exists():
        print(f"[PL Delete] File not found: {file_path}")
        raise HTTPException(
            status_code=404, 
            detail=f"File {filename} not found"
        )

    # Verify the file is actually in the expected directory
    if not file_path.is_relative_to(reports_dir):
        print(f"[PL Delete] File path not relative to reports dir")
        raise HTTPException(
            status_code=400, 
            detail="Invalid file path"
        )

    try:
        os.remove(file_path)
        print(f"[PL Delete] Successfully deleted: {filename}")
        return {
            "success": True,
            "message": f"Successfully deleted {filename}",
            "filename": filename
        }
    except Exception as e:
        print(f"[PL Delete] Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error deleting file: {str(e)}"
        )
