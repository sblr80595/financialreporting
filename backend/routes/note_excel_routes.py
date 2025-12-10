"""
API routes for generating Excel files from financial note markdown files.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from typing import Optional
from backend.services.note_excel_generator import NoteExcelGenerator

router = APIRouter()


class NoteExcelRequest(BaseModel):
    """Request model for note Excel generation."""
    company_name: str
    note_filename: str  # e.g., "Note_28_Employee_Benefits.md"
    period: Optional[str] = None


class NoteExcelResponse(BaseModel):
    """Response model for note Excel generation."""
    success: bool
    message: str
    output_file: Optional[str] = None
    note_number: Optional[str] = None
    note_title: Optional[str] = None


@router.post("/generate-excel", response_model=NoteExcelResponse)
async def generate_note_excel(request: NoteExcelRequest):
    """
    Generate Excel file from a markdown note file.
    
    This endpoint:
    1. Reads the markdown note file
    2. Extracts the main summary table (NOT GL breakdown)
    3. Creates a professionally formatted Excel file
    4. Saves in data/{company}/output/generated_notes_excel/
    
    Args:
        request: NoteExcelRequest with company name and note filename
        
    Returns:
        NoteExcelResponse with file path and metadata
    """
    try:
        # Construct paths based on actual structure: data/{company}/output/generated_notes/
        base_path = os.path.join("data", request.company_name, "output")
        markdown_path = os.path.join(base_path, "generated_notes", request.note_filename)
        excel_output_dir = os.path.join(base_path, "generated_notes_excel")
        
        # Check if markdown file exists
        if not os.path.exists(markdown_path):
            raise HTTPException(
                status_code=404,
                detail=f"Markdown file not found: {request.note_filename}"
            )
        
        # Generate Excel
        result = NoteExcelGenerator.generate_excel_from_markdown_file(
            markdown_file_path=markdown_path,
            output_dir=excel_output_dir,
            period=request.period
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return NoteExcelResponse(
            success=True,
            message=result["message"],
            output_file=result["output_file"],
            note_number=result.get("note_number"),
            note_title=result.get("note_title")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating note Excel: {str(e)}"
        )


@router.post("/generate-and-download-excel/{company_name}/{filename}")
async def generate_and_download_excel(company_name: str, filename: str):
    """
    Generate Excel from markdown and immediately return it for download.
    This is a convenience endpoint that combines generation and download.
    
    Args:
        company_name: Company name
        filename: Markdown filename (e.g., "Note_28_Employee_Benefits.md")
        
    Returns:
        FileResponse with the generated Excel file
    """
    try:
        # Construct paths based on actual structure: data/{company}/output/generated_notes/
        base_path = os.path.join("data", company_name, "output")
        markdown_path = os.path.join(base_path, "generated_notes", filename)
        excel_output_dir = os.path.join(base_path, "generated_notes_excel")
        
        # Check if markdown file exists
        if not os.path.exists(markdown_path):
            raise HTTPException(
                status_code=404,
                detail=f"Markdown file not found: {filename}"
            )
        
        # Generate Excel
        result = NoteExcelGenerator.generate_excel_from_markdown_file(
            markdown_file_path=markdown_path,
            output_dir=excel_output_dir,
            period=None  # Will be extracted from markdown
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        excel_file_path = result["output_file"]
        excel_filename = os.path.basename(excel_file_path)
        
        # Return the file for download
        return FileResponse(
            path=excel_file_path,
            filename=excel_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating and downloading Excel: {str(e)}"
        )


@router.get("/download-excel/{company_name}/{filename}")
async def download_note_excel(company_name: str, filename: str):
    """
    Download a generated note Excel file.
    
    Args:
        company_name: Company name
        filename: Excel filename to download
        
    Returns:
        FileResponse with the Excel file
    """
    try:
        file_path = os.path.join(
            "data",
            company_name,
            "output",
            "generated_notes_excel",
            filename
        )
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading file: {str(e)}"
        )


@router.get("/list-excel/{company_name}")
async def list_note_excel_files(company_name: str):
    """
    List all generated Excel files for a company.
    
    Args:
        company_name: Company name
        
    Returns:
        List of Excel files with metadata
    """
    try:
        excel_dir = os.path.join("data", company_name, "output", "generated_notes_excel")
        
        if not os.path.exists(excel_dir):
            return {"files": []}
        
        files = []
        for filename in os.listdir(excel_dir):
            if filename.endswith('.xlsx'):
                file_path = os.path.join(excel_dir, filename)
                stat = os.stat(file_path)
                
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": stat.st_ctime,
                    "modified_at": stat.st_mtime
                })
        
        return {"files": sorted(files, key=lambda x: x['modified_at'], reverse=True)}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )