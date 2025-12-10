# ============================================================================
# FILE: src/routes/generation_routes.py
# ============================================================================
"""Note generation API routes."""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.models.generation import (
    BatchGenerationRequest,
    BatchGenerationStatus,
    GenerationResponse,
    NoteGenerationRequest,
)
from backend.services.company_service import CompanyService
from backend.services.generation_service import GenerationService

router = APIRouter()


@router.post("/generate", response_model=GenerationResponse)
async def generate_single_note(request: NoteGenerationRequest):
    """Generate a single note for a company."""
    # Case-insensitive company lookup
    companies_dict = CompanyService.discover_companies()
    company_name_match = None
    for company_key in companies_dict:
        if company_key.lower() == request.company_name.lower():
            company_name_match = company_key
            break

    if not company_name_match:
        raise HTTPException(
            status_code=404, detail=f"Company '{request.company_name}' not found"
        )

    result = GenerationService.generate_single_note(
        company_name_match, request.note_number
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.post("/generate/batch")
async def generate_all_notes(
    request: BatchGenerationRequest, background_tasks: BackgroundTasks
):
    """Generate notes for a company in the background. Optionally filter by category_id."""
    print("🎯 Batch generation endpoint called!")
    print(f"   Request: company_name={request.company_name}, category_id={request.category_id}")

    companies_dict = CompanyService.discover_companies()
    print(f"   Available companies: {list(companies_dict.keys())}")

    # Case-insensitive company lookup
    company_name_match = None
    for company_key in companies_dict:
        if company_key.lower() == request.company_name.lower():
            company_name_match = company_key
            break

    if not company_name_match:
        print(f"   ❌ Company '{request.company_name}' not found!")
        raise HTTPException(
            status_code=404, detail=f"Company '{request.company_name}' not found"
        )

    print(f"   ✅ Matched company: {company_name_match}")

    batch_id = f"{company_name_match}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    GenerationService.batch_status[batch_id] = BatchGenerationStatus(
        status="pending", total_notes=0, completed_notes=0, results=[]
    )

    background_tasks.add_task(
        GenerationService.batch_generate_notes,
        company_name_match,
        batch_id,
        request.category_id,
    )

    return {
        "message": f"Batch generation started for {company_name_match}",
        "batch_id": batch_id,
        "status_url": f"/api/generate/batch/{batch_id}/status",
    }


@router.get("/generate/batch/{batch_id}/status", response_model=BatchGenerationStatus)
async def get_batch_status(batch_id: str):
    """Get the status of a batch generation process."""
    if batch_id not in GenerationService.batch_status:
        print(f"⚠️  Batch ID not found: {batch_id}")
        print(f"   Available batch IDs: {list(GenerationService.batch_status.keys())}")
        raise HTTPException(status_code=404, detail=f"Batch ID '{batch_id}' not found")

    current_status = GenerationService.batch_status[batch_id]
    print(f"📊 Batch status check: {batch_id}")
    print(f"   Status: {current_status.status}")
    print(f"   Progress: {current_status.completed_notes}/{current_status.total_notes}")
    
    return current_status


@router.get("/generated-notes/{company_name}")
async def list_generated_notes(company_name: str, category_id: str = None):
    """
    List all generated notes for a company, optionally filtered by category.

    Returns list of generated note files with metadata including:
    - filename
    - note_number
    - title
    - size_bytes
    - generated_at (timestamp)
    - download_url
    """
    companies_dict = CompanyService.discover_companies()
    company_name_match = None
    for company_key in companies_dict:
        if company_key.lower() == company_name.lower():
            company_name_match = company_key
            break

    if not company_name_match:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_name}' not found"
        )

    notes = GenerationService.list_generated_notes(company_name_match, category_id)

    return {
        "company_name": company_name_match,
        "category_id": category_id,
        "notes": notes,
        "count": len(notes)
    }


@router.get("/note-content/{company_name}/{filename}")
async def get_note_content(company_name: str, filename: str):
    """
    Get the content of a specific generated note file.

    Returns the markdown content of the note.
    """
    companies_dict = CompanyService.discover_companies()
    company_name_match = None
    for company_key in companies_dict:
        if company_key.lower() == company_name.lower():
            company_name_match = company_key
            break

    if not company_name_match:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_name}' not found"
        )

    content = GenerationService.get_note_content(company_name_match, filename)

    if content is None:
        raise HTTPException(
            status_code=404, detail=f"Note file '{filename}' not found"
        )

    return {
        "filename": filename,
        "content": content
    }


@router.get("/download-note/{company_name}/{filename}")
async def download_note(company_name: str, filename: str):
    """Download a specific generated note file."""
    from fastapi.responses import FileResponse

    from backend.config.settings import settings

    companies_dict = CompanyService.discover_companies()
    company_name_match = None
    for company_key in companies_dict:
        if company_key.lower() == company_name.lower():
            company_name_match = company_key
            break

    if not company_name_match:
        raise HTTPException(
            status_code=404, detail=f"Company '{company_name}' not found"
        )

    notes_dir = settings.get_entity_generated_notes_dir(company_name_match)
    file_path = notes_dir / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404, detail=f"Note file '{filename}' not found"
        )

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/markdown"
    )
