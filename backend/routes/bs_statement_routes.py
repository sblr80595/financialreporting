# ============================================================================
# FILE: backend/routes/bs_statement_routes.py
# ============================================================================
"""Balance Sheet generation API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.config.settings import settings
from backend.models.balance_sheet_models import (
    BSGenerationRequest,
    BSGenerationResponse,
)
from backend.services.bs_statement_service import BSStatementService
import os

router = APIRouter()


@router.get("/bs-statement-readiness/{company_name}")
async def check_bs_readiness(company_name: str):
    """
    Check if all required notes are available for Balance Sheet generation.

    This endpoint checks if the entity has generated all required notes for:
    - Non-current assets (notes 3, 4, 5, 7)
    - Current assets (notes 8, 9, 10, 11, 12, 13, 7)
    - Equity (notes 14, 15)
    - Non-current liabilities (notes 17, 18, 6)
    - Current liabilities (notes 16, 17, 18, 19, 20, 21, 22, 23)

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
        readiness = BSStatementService.check_bs_readiness(company_name)
        return readiness
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking Balance Sheet readiness: {str(e)}"
        )


@router.post("/generate-bs-statement", response_model=BSGenerationResponse)
async def generate_bs_statement(request: BSGenerationRequest):
    """
    Generate Balance Sheet from generated notes.

    This endpoint:
    1. Checks if all required notes are available
    2. Extracts total amounts from each note markdown file
    3. Compiles them into a complete Balance Sheet
    4. Calculates Assets = Equity + Liabilities
    5. Exports to Excel format with proper formatting
    6. Saves in reports/{company_name}/ directory

    All amounts are displayed as positive values (no negative signs).

    Args:
        request: BSGenerationRequest with company name and date

    Returns:
        BSGenerationResponse with statement data and file path
    """
    # First check if ready
    readiness = BSStatementService.check_bs_readiness(request.company_name)

    if not readiness["is_ready"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot generate Balance Sheet. Not all required notes are available.",
                "missing_notes": readiness["missing_notes"],
                "completeness": readiness["completeness_percentage"],
            },
        )

    result = BSStatementService.generate_bs_statement(
        company_name=request.company_name,
        as_at_date=request.as_at_date,
        note_numbers=request.note_numbers,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.get("/download-bs-statement/{company_name}")
async def download_latest_bs_statement(company_name: str):
    """
    Download the most recently generated Balance Sheet Excel file.

    Args:
        company_name: Name of the company

    Returns:
        Excel file download
    """
    from backend.services.path_service import PathService
    path_service = PathService(company_name)
    reports_dir = path_service.get_financial_statements_dir(company_name) / "BS"

    if not reports_dir.exists():
        raise HTTPException(
            status_code=404, detail=f"No Balance Sheets found for {company_name}"
        )

    # Find the most recent Balance Sheet file (both old and new naming)
    bs_files = list(reports_dir.glob("BS_Statement_*.xlsx")) + list(reports_dir.glob("Balance_Sheet_*.xlsx"))

    if not bs_files:
        raise HTTPException(
            status_code=404, detail=f"No Balance Sheets found for {company_name}"
        )

    latest_file = max(bs_files, key=lambda p: p.stat().st_mtime)

    return FileResponse(
        path=str(latest_file),
        filename=latest_file.name,  # Use the actual filename
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/bs-statements-list/{company_name}")
async def list_bs_statements(company_name: str):
    """
    List all generated Balance Sheets for a company with metadata.

    Args:
        company_name: Name of the company

    Returns:
        List of generated statements with timestamps and file paths
    """
    from backend.services.path_service import PathService
    path_service = PathService(company_name)
    reports_dir = path_service.get_financial_statements_dir(company_name) / "BS"

    if not reports_dir.exists():
        return {"company_name": company_name, "files": [], "statements": [], "count": 0}

    # Support both old and new naming conventions
    bs_files = list(reports_dir.glob("BS_Statement_*.xlsx")) + list(reports_dir.glob("Balance_Sheet_*.xlsx"))

    statements = []
    for file_path in sorted(bs_files, key=lambda p: p.stat().st_mtime, reverse=True):
        stat = file_path.stat()
        statements.append({
            "filename": file_path.name,
            "file_path": str(file_path),
            "size_bytes": stat.st_size,
            "generated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "download_url": f"/api/bs-statement/{company_name}/download/{file_path.name}",
        })

    return {
        "company_name": company_name,
        "files": statements,  # For consistency with other endpoints
        "statements": statements,  # For backwards compatibility
        "count": len(statements),
        "latest": statements[0] if statements else None,
    }

@router.get("/bs-statement/{company_name}/download/{filename}")
async def download_bs_statement_file(company_name: str, filename: str):
    """
    Download a specific Balance Sheet file.

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
    reports_dir = path_service.get_financial_statements_dir(company_name) / "BS"
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

@router.delete("/bs-statement/{company_name}/{filename}")
async def delete_bs_statement(company_name: str, filename: str):
    """
    Delete a specific Balance Sheet file.

    Args:
        company_name: Name of the company
        filename: Name of the file to delete

    Returns:
        Success message
    """
    from backend.services.path_service import PathService
    
    print(f"[BS Delete] Attempting to delete: {filename} for company: {company_name}")
    
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        print(f"[BS Delete] Invalid filename detected: {filename}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid filename"
        )
    
    path_service = PathService(company_name)
    reports_dir = path_service.get_financial_statements_dir(company_name) / "BS"
    file_path = reports_dir / filename
    
    print(f"[BS Delete] Looking for file at: {file_path}")

    if not file_path.exists():
        print(f"[BS Delete] File not found: {file_path}")
        raise HTTPException(
            status_code=404, 
            detail=f"File {filename} not found"
        )

    # Verify the file is actually in the expected directory
    if not file_path.is_relative_to(reports_dir):
        print(f"[BS Delete] File path not relative to reports dir")
        raise HTTPException(
            status_code=400, 
            detail="Invalid file path"
        )

    try:
        os.remove(file_path)
        print(f"[BS Delete] Successfully deleted: {filename}")
        return {
            "success": True,
            "message": f"Successfully deleted {filename}",
            "filename": filename
        }
    except Exception as e:
        print(f"[BS Delete] Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error deleting file: {str(e)}"
        )
