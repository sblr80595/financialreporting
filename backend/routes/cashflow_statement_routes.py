# ============================================================================
# FILE: backend/routes/cashflow_statement_routes.py
# ============================================================================
"""Cash Flow Statement generation API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.models.cashflow_models import (
    CashFlowGenerationRequest,
    CashFlowGenerationResponse,
)
from backend.services.cashflow_statement_service import CashFlowStatementService
from backend.services.path_service import PathService

router = APIRouter()


@router.get("/cashflow-statement-readiness/{company_name}")
async def check_cashflow_readiness(company_name: str):
    """
    Check if Cash Flow Statement markdown file exists for the entity.

    This endpoint checks if the entity has generated the Cash Flow Statement
    markdown file (Note_CASHFLOW_*.md). This file must be generated first
    before creating the Excel template.

    Returns:
        - is_ready: True if markdown file is available
        - markdown_file: Path to the markdown file
        - period: Period information extracted from the file
        - generated_at: When the file was created
        - message: Status message

    Args:
        company_name: Name of the company/entity

    Returns:
        Readiness status with detailed information
    """
    try:
        readiness = CashFlowStatementService.check_cashflow_readiness(company_name)
        return readiness
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error checking Cash Flow readiness: {str(e)}"
        )


@router.post("/generate-cashflow-template", response_model=CashFlowGenerationResponse)
async def generate_cashflow_template(request: CashFlowGenerationRequest):
    """
    Generate Cash Flow Statement Excel template from markdown file.

    This endpoint:
    1. Checks if the Cash Flow markdown file (Note_CASHFLOW_*.md) exists
    2. Parses the markdown content to extract:
       - Operating activities (Profit before tax, Adjustments, Working capital changes)
       - Investing activities (PPE purchases, Investments, Interest, Dividends)
       - Financing activities (Borrowings, Lease payments, Interest paid)
    3. Creates a formatted Excel file with:
       - Professional formatting (borders, fonts, alignments)
       - Proper section headers
       - Calculated totals and reconciliation
    4. Saves in financial_statements/{company_name}/CashFlow/ directory

    Args:
        request: CashFlowGenerationRequest with company name and optional period

    Returns:
        CashFlowGenerationResponse with statement data and file path

    Raises:
        HTTPException 400: If markdown file doesn't exist
        HTTPException 500: If generation fails
    """
    # Generate the Excel template
    result = CashFlowStatementService.generate_cashflow_excel(
        company_name=request.company_name,
        period_ended=request.period_ended
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400, 
            detail=result.get("message", "Failed to generate Cash Flow template")
        )

    return CashFlowGenerationResponse(
        success=True,
        message=result["message"],
        output_file=result["output_file"],
        company_name=result["company_name"],
        period_ended=result["period_ended"],
        source_markdown=result.get("source_markdown")
    )


@router.get("/download-cashflow-template/{company_name}")
async def download_latest_cashflow_template(company_name: str):
    """
    Download the most recently generated Cash Flow Statement Excel file.

    Args:
        company_name: Name of the company

    Returns:
        Excel file download

    Raises:
        HTTPException 404: If no Cash Flow statements found
    """
    path_service = PathService(company_name)
    cashflow_dir = path_service.get_financial_statements_dir(company_name) / "CashFlow"

    if not cashflow_dir.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"No Cash Flow statements found for {company_name}"
        )

    # Find the most recent Cash Flow statement file
    cashflow_files = list(cashflow_dir.glob("CashFlow_Statement_*.xlsx"))

    if not cashflow_files:
        raise HTTPException(
            status_code=404, 
            detail=f"No Cash Flow statements found for {company_name}"
        )

    latest_file = max(cashflow_files, key=lambda p: p.stat().st_mtime)

    return FileResponse(
        path=str(latest_file),
        filename=f"CashFlow_Statement_{company_name}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/cashflow-statements-list/{company_name}")
async def list_cashflow_statements(company_name: str):
    """
    List all generated Cash Flow statements for a company with metadata.

    Args:
        company_name: Name of the company

    Returns:
        List of generated statements with details:
        - filename: Name of the file
        - path: Full path to the file
        - generated_at: Timestamp when file was created
        - size: File size in bytes

    Example response:
    {
        "company_name": "ABC Company",
        "statements": [
            {
                "filename": "CashFlow_Statement_20250105_143022.xlsx",
                "path": "/path/to/file.xlsx",
                "generated_at": "2025-01-05T14:30:22",
                "size": 15234
            }
        ],
        "count": 1
    }
    """
    try:
        result = CashFlowStatementService.list_cashflow_statements(company_name)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error listing Cash Flow statements: {str(e)}"
        )


@router.delete("/cashflow-statement/{company_name}/{filename}")
async def delete_cashflow_statement(company_name: str, filename: str):
    """
    Delete a specific Cash Flow statement file.

    Args:
        company_name: Name of the company
        filename: Name of the file to delete

    Returns:
        Success message

    Raises:
        HTTPException 404: If file not found
        HTTPException 500: If deletion fails
    """
    print(f"[CashFlow Delete] Attempting to delete: {filename} for company: {company_name}")
    
    try:
        path_service = PathService(company_name)
        cashflow_dir = path_service.get_financial_statements_dir(company_name) / "CashFlow"
        
        file_path = cashflow_dir / filename
        
        print(f"[CashFlow Delete] Looking for file at: {file_path}")

        if not file_path.exists():
            print(f"[CashFlow Delete] File not found: {file_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Cash Flow statement file not found: {filename}"
            )

        # Delete the file
        file_path.unlink()
        print(f"[CashFlow Delete] Successfully deleted: {filename}")

        return {
            "success": True,
            "message": f"Successfully deleted {filename}",
            "company_name": company_name,
            "deleted_file": filename
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CashFlow Delete] Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting Cash Flow statement: {str(e)}"
        )


@router.get("/cashflow-statement/{company_name}/download/{filename}")
async def download_cashflow_statement_file(company_name: str, filename: str):
    """
    Download a specific Cash Flow statement file.

    Args:
        company_name: Name of the company
        filename: Name of the file to download

    Returns:
        File response

    Raises:
        HTTPException 404: If file not found
        HTTPException 400: If invalid filename
    """
    from fastapi.responses import FileResponse
    
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )
    
    try:
        path_service = PathService(company_name)
        cashflow_dir = path_service.get_financial_statements_dir(company_name) / "CashFlow"
        file_path = cashflow_dir / filename

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Cash Flow statement file not found: {filename}"
            )

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading Cash Flow statement: {str(e)}"
        )


@router.get("/cashflow-markdown/{company_name}")
async def get_cashflow_markdown(company_name: str):
    """
    Get the content of the Cash Flow Statement markdown file.

    This is useful for debugging or previewing the source data
    before generating the Excel template.

    Args:
        company_name: Name of the company

    Returns:
        Markdown content and metadata

    Raises:
        HTTPException 404: If markdown file not found
    """
    try:
        readiness = CashFlowStatementService.check_cashflow_readiness(company_name)

        if not readiness["is_ready"]:
            raise HTTPException(
                status_code=404,
                detail="Cash Flow Statement markdown file not found"
            )

        # Read the markdown file
        with open(readiness["markdown_file"], 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "company_name": company_name,
            "markdown_file": readiness["markdown_file"],
            "content": content,
            "period": readiness.get("period"),
            "generated_at": readiness.get("generated_at"),
            "file_size": readiness.get("file_size")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading markdown file: {str(e)}"
        )