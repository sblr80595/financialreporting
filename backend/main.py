
from pathlib import Path
import json
import logging
import os
import traceback
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.config.entities import EntityConfig, get_entities_list
from backend.config.period_config import period_config
from backend.config.settings import settings
from backend.models.response_models import FileUploadResponse, ProcessingStatus
from backend.models.responses import HealthCheckResponse, ErrorResponse
from backend.exceptions import (
    FinancialReportingException,
    EntityNotFoundException,
    FileNotFoundException,
    ValidationException
)
from backend.middleware.error_handlers import register_exception_handlers
from backend.services.audit_service import audit_logger
from backend.routes import api_router
from backend.routes.pl_statement_routes import router as pl_router
from backend.routes.bs_statement_routes import router as bs_router
from backend.routes.period_routes import router as period_router

# Import Trial Balance services
from backend.services.ai_orchestrator_service import AIOrchestratorService

# Import Note Generation services and models
from backend.services.company_service import CompanyService
from backend.services.file_service import FileService
from backend.services.financial_statement_service import FinancialStatementService
from backend.services.mapping_service import MappingService
from backend.services.path_service import PathService
from backend.services.validation_service import ValidationService
from backend.routes import pnl_finalyzer_routes
from backend.routes import pnl_schedule_finalyzer_routes
from backend.routes.bs_finalyzer_routes import router as bs_finalyzer_router
from backend.routes.bs_schedule_finalyzer_routes import router as bs_schedule_router

from backend.routes.equity_finalyzer_routes import router as equity_finalyzer_router
from backend.routes import cashflow_statement_routes

from backend.routes import cashflow_finalyzer_routes
from backend.routes.adjustments_routes import router as adjustments_router
from backend.routes.currency_routes import router as currency_router
from backend.routes.sap_routes import router as sap_router
from backend.routes.note_excel_routes import router as note_excel_generator
from backend.routes.statement_viewer_routes import router as statement_viewer_router

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging with enhanced format for better debugging and audit trails
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Silence noisy libraries
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('httpcore').setLevel(logging.ERROR)
logging.getLogger('google').setLevel(logging.ERROR)

# Create a main application logger
logger = logging.getLogger(__name__)

# ============================================================================
# END LOGGING CONFIGURATION
# ============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="Financial Automation Platform API",
    description="Professional-grade financial reporting and automation platform with comprehensive error handling and audit trails",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Register exception handlers for comprehensive error handling
register_exception_handlers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services will be initialized per request with entity context
# Global service instances for stateless operations
file_service = FileService()
validation_service = ValidationService()
mapping_service = MappingService()

# Application startup timestamp for monitoring and health checks
app_start_time = time.time()

# In-memory storage for processing status (in production, use Redis or database)
processing_status: Dict[str, ProcessingStatus] = {}

# Include authentication and note generation routes with /api prefix
app.include_router(api_router, prefix="/api")
app.include_router(pl_router, prefix="/api", tags=["P&L Statement"])
app.include_router(bs_router, prefix="/api", tags=["Balance Sheet"])
app.include_router(
    cashflow_statement_routes.router,
    prefix="/api",
    tags=["Cash Flow Statement"]
)
app.include_router(period_router, prefix="/api", tags=["Period Management"])
app.include_router(
    pnl_finalyzer_routes.router,
    prefix="/api",
    tags=["PNL Finalyzer"],
)
app.include_router(
    pnl_schedule_finalyzer_routes.router,
    prefix="/api",
    tags=["PNL Schedule Finalyzer"],
)
app.include_router(bs_finalyzer_router, prefix="/api", tags=["BS Finalyzer"])
app.include_router(bs_schedule_router, prefix="/api", tags=["BS Schedule"])


app.include_router(equity_finalyzer_router,  prefix="/api", tags=["Equity Schedule"])

app.include_router(
    cashflow_finalyzer_routes.router,
    prefix="/api",
    tags=["Cash Flow Finalyzer"]
)
app.include_router(currency_router, prefix="/api", tags=["Currency"])
app.include_router(adjustments_router, prefix="/api", tags=["Adjustments Analysis"])
app.include_router(sap_router, prefix="/api", tags=["SAP Integration"])
app.include_router(note_excel_generator, prefix="/api/notes", tags=["Note Excel generation"])
app.include_router(statement_viewer_router, prefix="/api", tags=["Statement Viewer"])


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to track request processing time"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Financial Automation Platform API",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "trial_balance_processing": "Available",
            "note_generation": "Available",
            "authentication": "JWT Bearer Token",
            "bs_finalyzer": "Available",
            "audit_logging": "Enabled",
            "error_tracking": "Enabled"
        },
        "endpoints": {
            "auth": "/auth/login, /auth/refresh, /auth/me",
            "companies": "/companies (requires auth)",
            "note_generation": "/generate (requires auth)",
            "trial_balance": "/api/upload/trial-balance, /api/process/adjustments",
            "bs_finalyzer": "/api/generate-bs-finalyzer",
            "health": "/api/health",
            "docs": "/api/docs"
        }
    }


@app.get("/api/test-upload")
async def test_upload():
    """Test endpoint to verify API is responding"""
    return {
        "status": "ok",
        "message": "Upload endpoint is accessible",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """Detailed health check with response model validation"""
    try:
        companies = CompanyService.discover_companies()

        is_valid, error_msg = settings.validate_llm_config()
        llm_status = "healthy" if is_valid else f"error: {error_msg}"

        uptime = time.time() - app_start_time

        return HealthCheckResponse(
            status="healthy",
            version="2.0.0",
            services={
                "api": "healthy",
                "llm": llm_status,
                "file_system": "healthy",
                "companies_discovered": str(len(companies))
            },
            uptime_seconds=uptime
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": "2.0.0",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize directories on startup"""
    # Print startup information to console only (not logged)
    print("\n" + "=" * 70)
    print("🚀 Financial Automation Platform API Starting...")
    print("=" * 70)
    
    # Create all necessary directories
    print("📁 Creating necessary directories...")
    settings.CONFIG_DIR.mkdir(exist_ok=True)
    #settings.REPORTS_DIR.mkdir(exist_ok=True)
    #settings.DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    print("   ✅ Base directories created")

    # NOTE: Removed global default period setting to allow entity-specific auto-detection
    # Users can set period per entity via API: POST /api/periods/set {"period_key": "mar_2025"}
    # Or period will be auto-detected from entity's trial balance file
    print("📅 Period will be auto-detected per entity from trial balance files")
    print("   💡 To set manually: POST /api/periods/set {\"period_key\": \"<period>\"}")

    # Create entity directories (cpm, hausen, etc.)
    print("📁 Creating entity directories...")

    for entity in ["cpm", "analisa_resource", "neoscience_sdn", "lifeline_holdings", "lifeline_diagnostics","everlife_ph_holding","ttpl_fs","cpc_diagnostics_india"]:
        entity_input = settings.get_entity_input_dir(entity)
        entity_output = settings.get_entity_output_dir(entity)
        entity_input.mkdir(parents=True, exist_ok=True)
        entity_output.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {entity}")

    # Print startup information
    print("🔍 Discovering companies...")
    companies = CompanyService.discover_companies()
    
    print(f"\n{'=' * 70}")
    print("Financial Automation Platform API Started (v2.0.0)")
    print(f"{'=' * 70}")
    print(f"📊 Found {len(companies)} companies:")
    for name, details in companies.items():
        print(f"  - {name}: {len(details['notes'])} notes")
        for category, notes in details["notes_by_category"].items():
            print(f"    └─ {category}: {len(notes)} notes")
    print(f"{'=' * 70}")
    print("🚀 Features: TB Processing | Note Generation | P&L Statements")
    print(f"📝 Individual logs saved to: {LOGS_DIR}/ folder")
    print(f"📝 Log format: YYYYMMDD_HHMMSS_NoteXX_NoteName_Company.log")
    print(f"{'=' * 70}\n")


# Entity Management
@app.get("/api/entities")
async def get_entities():
    """Get list of available entities from centralized configuration"""
    # Get entities from centralized config ONLY
    # No longer merging with filesystem to maintain control over visible entities
    entities = get_entities_list()
    
    # OLD CODE (commented out - was auto-discovering entities from filesystem):
    # # Also check for any additional entities in data folder
    # existing_entity_names = file_service.get_available_entities()
    #
    # # Merge: prioritize configured entities, add any new ones from filesystem
    # entity_codes = {e["code"] for e in entities}
    # for entity_name in existing_entity_names:
    #     # Normalize the entity name (handles legacy codes like cpm_my)
    #     normalized_code = EntityConfig.normalize_entity_code(entity_name)
    #
    #     # Only add if not already in configured entities
    #     if normalized_code not in entity_codes:
    #         entities.append({
    #             "code": normalized_code,
    #             "name": entity_name.upper(),
    #             "short_code": normalized_code,
    #             "description": f"{entity_name} entity (discovered from filesystem)"
    #         })
    #     entity_codes.add(normalized_code)

    return entities


# File Management
@app.get("/api/files/{entity}")
async def list_entity_files(entity: str):
    """List all files for an entity"""
    try:
        files = file_service.list_available_files(entity)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/api/files/{entity}/check")
async def check_file_exists(
    entity: str,
    folder_type: str,
    filename: str
):
    """Check if a file exists"""
    try:
        file_info = file_service.check_file_exists(filename, folder_type, entity)
        return file_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/files/{entity}")
async def delete_file(
    entity: str,
    folder_type: str,
    filename: str
):
    """Delete a file"""
    try:
        success = file_service.delete_file(filename, folder_type, entity)
        if success:
            return {"success": True, "message": f"File {filename} deleted successfully"}

        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/files/{entity}/preview")
async def preview_file(
    entity: str,
    folder_type: str,
    filename: str,
    rows: int = 50
):
    """Preview file content (first N rows)"""
    try:
        file_path = file_service.get_file_path(filename, folder_type, entity)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Read Excel file
        df = pd.read_excel(file_path)

        # Replace NaN and infinity values with None for JSON serialization
        df = df.replace([float('inf'), float('-inf')], None)
        df = df.where(pd.notnull(df), None)
        
        # Clean column names - replace NaN with empty string or index
        df.columns = [str(col) if pd.notna(col) else f"Column_{i}" for i, col in enumerate(df.columns)]

        # Limit rows for preview
        preview_df = df.head(rows)

        # Convert to list of lists for easier rendering
        rows_data = preview_df.values.tolist()

        return {
            "filename": filename,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "rows": rows_data,
            "preview_count": len(preview_df)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/files/{entity}/download")
async def download_file(
    entity: str,
    folder_type: str,
    filename: str
):
    """Download a specific file"""
    try:
        file_path = file_service.get_file_path(filename, folder_type, entity)
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
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/api/files/{entity}/check")
async def check_file_exists(
    entity: str,
    folder_type: str,
    filename: str
):
    """Check if a file exists"""
    try:
        file_info = file_service.check_file_exists(filename, folder_type, entity)
        return file_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/files/{entity}")
async def delete_file(
    entity: str,
    folder_type: str,
    filename: str
):
    """Delete a file"""
    try:
        success = file_service.delete_file(filename, folder_type, entity)
        if success:
            return {"success": True, "message": f"File {filename} deleted successfully"}

        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/files/{entity}/download")
async def download_file(
    entity: str,
    folder_type: str,
    filename: str
):
    """Download a specific file"""
    try:
        file_path = file_service.get_file_path(filename, folder_type, entity)
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
        raise HTTPException(status_code=500, detail=str(e)) from e

# File Upload Endpoints


@app.post("/api/upload/trial-balance")
async def upload_trial_balance(
    entity: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload trial balance file"""
    try:
        # Normalize entity name using centralized config
        entity = EntityConfig.normalize_entity_code(entity)

        print("\n📤 Upload trial balance request:")
        print(f"   Entity: {entity}")
        print(f"   Filename: {file.filename}")
        print(f"   Content-Type: {file.content_type}")

        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls', '.xlsb')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xls, .xlsb) are allowed"
            )

        # Ensure entity directory structure exists
        path_service = PathService(entity)
        path_service.create_entity_structure(entity)
        print("   ✅ Entity structure verified")

        # Save file
        print("   Saving file...")
        file_path = await file_service.save_trial_balance(file, entity)
        print(f"   ✅ File saved to: {file_path}")

        # Validate trial balance
        print("   Validating trial balance...")
        try:
            validation_result = await validation_service.validate_trial_balance(file_path)
            print("   ✅ Validation complete")
        except Exception as val_error:
            print(f"   ⚠️  Validation warning: {str(val_error)}")
            validation_result = {
                "valid": False,
                "error": str(val_error),
                "checks": []
            }

        return FileUploadResponse(
            success=True,
            message="Trial balance uploaded successfully",
            file_path=file_path,
            validation_result=validation_result
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Error uploading trial balance: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload trial balance: {str(e)}") from e


@app.post("/api/upload/config")
async def upload_config_file(
    entity: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload config file (e.g., mapping file) to entity's config folder"""
    try:
        # Normalize entity name
        entity = EntityConfig.normalize_entity_code(entity)

        print("\n📤 Upload config file request:")
        print(f"   Entity: {entity}")
        print(f"   Filename: {file.filename}")

        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls', '.xlsb')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xls, .xlsb) are allowed"
            )

        # Ensure entity directory structure exists
        path_service = PathService(entity)
        path_service.create_entity_structure(entity)

        # Get config directory
        config_dir = path_service.get_config_dir(entity)
        config_dir.mkdir(parents=True, exist_ok=True)

        # Always save as standard filename for mapping files
        # This ensures consistency across all entities
        standard_filename = "glcode_major_minor_mappings.xlsx"
        file_path = config_dir / standard_filename
        
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)

        print(f"   ✅ Config file saved as: {file_path}")

        return {
            "success": True,
            "message": f"Mapping file uploaded and saved as {standard_filename}",
            "filename": standard_filename,
            "original_filename": file.filename,
            "filepath": str(file_path),
            "entity": entity,
            "folder": "config"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Error uploading config file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload config file: {str(e)}") from e


@app.post("/api/upload/adjustments")
async def upload_adjustments(
    files: List[UploadFile] = File(...),
    entity: str = Form(...)
):
    """Upload adjustment files"""
    try:
        saved_files = []
        for file in files:
            if not file.filename.endswith(('.xlsx', '.xls', '.xlsb')):
                continue

            file_path = await file_service.save_adjustment_file(file, entity)
            saved_files.append({
                "filename": file.filename,
                "path": file_path,
                "size": os.path.getsize(file_path)
            })

        return {
            "success": True,
            "message": f"Uploaded {len(saved_files)} adjustment files",
            "files": saved_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# Processing Endpoints


@app.post("/api/process/adjustments")
async def process_adjustments(
    background_tasks: BackgroundTasks,
    entity: str = Form(...),
    period_key: Optional[str] = Form(None),
    period_column: Optional[str] = Form(None)
):
    """Start AI-powered adjustment processing"""
    try:
        # Apply period selection if provided (so subprocess sees correct period)
        from backend.config.period_config import period_config
        if period_key:
            try:
                period_config.set_period(period_key)
            except Exception:
                pass
        elif period_column:
            try:
                period_config.set_period_column(period_column)
            except Exception:
                pass

        # Generate unique processing ID
        processing_id = str(uuid.uuid4())

        # Initialize processing status
        processing_status[processing_id] = ProcessingStatus(
            id=processing_id,
            status="started",
            progress=0,
            message="Starting adjustment processing...",
            entity=entity,
            start_time=datetime.now().isoformat()
        )

        # Start background processing
        background_tasks.add_task(
            run_adjustment_processing,
            processing_id,
            entity
        )

        return {
            "processing_id": processing_id,
            "status": "started",
            "message": "Adjustment processing started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/process/status/{processing_id}")
async def get_processing_status(processing_id: str):
    """Get processing status"""
    if processing_id not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")

    return processing_status[processing_id]


@app.get("/api/adjustments/details/{processing_id}")
async def get_adjustment_details(processing_id: str):
    """Get detailed information about adjustments after processing"""
    if processing_id not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")

    status = processing_status[processing_id]

    if status.status != "completed":
        raise HTTPException(status_code=400, detail="Processing not completed yet")

    try:
        entity = status.entity
        ai_service = AIOrchestratorService(entity)

        # Get adjustment results
        adjustments = ai_service.parse_adjustment_results(entity)
        output_files = ai_service.check_output_files(entity)

        # Build detailed response
        # Note: Individual reconciliation files are no longer generated
        # Only the final adjusted_trialbalance.xlsx and other actual output files are shown
        path_service = PathService(entity)
        adjusted_tb_dir = path_service.get_adjusted_tb_dir(entity)

        # Get all actual files from the output directory
        actual_output_files = []
        if adjusted_tb_dir.exists():
            for file_path in adjusted_tb_dir.glob("*.xlsx"):
                if file_path.is_file():
                    file_stat = file_path.stat()
                    actual_output_files.append({
                        "filename": file_path.name,
                        "file_size": file_stat.st_size,
                        "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        "download_url": f"/api/adjustments/download/{entity}/{file_path.name}"
                    })

        # Check if final adjusted trial balance exists
        final_tb_path = adjusted_tb_dir / "adjusted_trialbalance.xlsx"
        final_tb_exists = final_tb_path.exists()
        
        # Adjustment summary (entity-specific)
        normalized_entity = EntityConfig.normalize_entity_code(entity)
        if normalized_entity == "lifeline_diagnostics":
            adjustment_config = [
                {"id": 5, "name": "GT India audit adjustments"}
            ]
        else:
            adjustment_config = [
                {"id": 1, "name": "Entries not considered in correct period"},
                {"id": 2, "name": "Roll back of audit adjustments"},
                {"id": 3, "name": "Roll forward entries"},
                {"id": 4, "name": "Interco adjustments"},
                {"id": 5, "name": "GT India audit adjustments"},
                {"id": 6, "name": "Reclassification entries"}
            ]

        # Mark all adjustments as applied if final TB exists
        adjustment_details = []
        for config in adjustment_config:
            adjustment_details.append({
                "id": config["id"],
                "name": config["name"],
                "status": "completed" if final_tb_exists else "pending"
            })

        # Check for final adjusted trial balance
        final_tb_path = adjusted_tb_dir / "adjusted_trialbalance.xlsx"
        final_tb_exists = final_tb_path.exists()

        # Get file details if it exists
        final_tb_details = None
        if final_tb_exists:
            file_stat = final_tb_path.stat()

            # Get timestamps
            created_at = datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()

            # Try to read the file to get row count
            try:
                df = pd.read_excel(final_tb_path)
                row_count = len(df)
                column_count = len(df.columns)
                columns = df.columns.tolist()
            except Exception:
                row_count = None
                column_count = None
                columns = []

            final_tb_details = {
                "exists": True,
                "filename": "adjusted_trialbalance.xlsx",
                "file_size": file_stat.st_size,
                "file_size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                "created_at": created_at,
                "modified_at": modified_at,
                "row_count": row_count,
                "column_count": column_count,
                "columns": columns,
                "download_url": f"/api/adjustments/download/{entity}/adjusted_trialbalance.xlsx",
                "view_url": f"/api/adjustments/preview/{entity}/adjusted_trialbalance.xlsx"
            }
        else:
            final_tb_details = {
                "exists": False,
                "filename": "adjusted_trialbalance.xlsx",
                "download_url": None,
                "view_url": None
            }

        # Determine if all adjustments succeeded
        # We no longer generate individual reconciliation files; success is based on final TB
        all_completed = final_tb_exists

        return {
            "processing_id": processing_id,
            "entity": entity,
            "status": status.status,
            "success": all_completed,
            "message": "✅ All adjustments applied successfully! Adjusted Trial Balance is ready." if all_completed else "⚠️ Some adjustments failed or files are missing.",
            "adjustments": adjustment_details,
            "summary": {
                "total_adjustments": len(adjustment_config),
                "completed_adjustments": len(adjustment_config) if final_tb_exists else 0,
                "total_output_files": len(output_files),
                "final_trial_balance": final_tb_details},
            "next_steps": {
                "available": all_completed,
                "next_step": "map_categories",
                "next_step_label": "Step 4: Map Major/Minor Categories",
                "next_step_description": "Map GL Codes to Major and Minor categories using glcode_major_minor_mappings.xlsx",
                "next_step_url": f"/api/mapping/start/{entity}" if all_completed else None},
            "output_files": output_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/adjustments/summary/{entity}")
async def get_adjustment_summary(entity: str):
    """Get adjustment summary for an entity (works without processing_id)"""
    try:
        path_service = PathService(entity)
        adjusted_tb_dir = path_service.get_adjusted_tb_dir(entity)

        # Get all actual files from the output directory
        actual_output_files = []
        if adjusted_tb_dir.exists():
            for file_path in adjusted_tb_dir.glob("*.xlsx"):
                if file_path.is_file():
                    file_stat = file_path.stat()
                    actual_output_files.append({
                        "filename": file_path.name,
                        "file_size": file_stat.st_size,
                        "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        "download_url": f"/api/adjustments/download/{entity}/{file_path.name}"
                    })

        # Check if final adjusted trial balance exists
        final_tb_path = adjusted_tb_dir / "adjusted_trialbalance.xlsx"
        final_tb_exists = final_tb_path.exists()
        
        # Adjustment summary (entity-specific)
        normalized_entity = EntityConfig.normalize_entity_code(entity)
        if normalized_entity == "lifeline_diagnostics":
            adjustment_config = [
                {"id": 5, "name": "GT India audit adjustments"}
            ]
        else:
            adjustment_config = [
                {"id": 1, "name": "Entries not considered in correct period"},
                {"id": 2, "name": "Roll back of audit adjustments"},
                {"id": 3, "name": "Roll forward entries"},
                {"id": 4, "name": "Interco adjustments"},
                {"id": 5, "name": "GT India audit adjustments"},
                {"id": 6, "name": "Reclassification entries"}
            ]

        # Mark all adjustments as applied if final TB exists
        adjustment_details = []
        for config in adjustment_config:
            adjustment_details.append({
                "id": config["id"],
                "name": config["name"],
                "status": "completed" if final_tb_exists else "pending"
            })

        # Check final adjusted trial balance
        if final_tb_exists:
            file_stat = final_tb_path.stat()
            df = pd.read_excel(final_tb_path)
            row_count = len(df)
            column_count = len(df.columns)
            columns = df.columns.tolist()
            file_size_mb = file_stat.st_size / (1024 * 1024)
            created_at = datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()

            final_tb_details = {
                "exists": True,
                "filename": "adjusted_trialbalance.xlsx",
                "file_size_mb": file_size_mb,
                "created_at": created_at,
                "modified_at": modified_at,
                "row_count": row_count,
                "column_count": column_count,
                "columns": columns,
                "download_url": f"/api/adjustments/download/{entity}/adjusted_trialbalance.xlsx",
                "view_url": f"/api/adjustments/preview/{entity}/adjusted_trialbalance.xlsx"
            }
        else:
            final_tb_details = {
                "exists": False,
                "filename": "adjusted_trialbalance.xlsx",
                "download_url": None,
                "view_url": None
            }

        # Determine if all adjustments succeeded
        all_completed = final_tb_exists

        return {
            "entity": entity,
            "status": "completed" if all_completed else "pending",
            "success": all_completed,
            "message": "✅ All adjustments applied successfully! Adjusted Trial Balance is ready." if all_completed else "⚠️ Adjustments not yet applied.",
            "adjustments": adjustment_details,
            "output_files": actual_output_files,
            "summary": {
                "total_adjustments": len(adjustment_config),
                "completed_adjustments": len(adjustment_config) if final_tb_exists else 0,
                "total_output_files": len(actual_output_files),
                "final_trial_balance": final_tb_details
            },
            "next_steps": {
                "available": all_completed,
                "next_step": "map_categories",
                "next_step_label": "Step 4: Map Major/Minor Categories",
                "next_step_description": "Map GL Codes to Major and Minor categories using glcode_major_minor_mappings.xlsx",
                "next_step_url": f"/api/mapping/start/{entity}" if all_completed else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/adjustments/download/{entity}/{filename}")
async def download_adjustment_file(entity: str, filename: str):
    """Download adjustment output file"""
    try:
        path_service = PathService(entity)

        # Security check - only allow downloading from adjusted_tb directory
        adjusted_tb_dir = path_service.get_adjusted_tb_dir(entity)
        file_path = adjusted_tb_dir / filename

        # Prevent directory traversal
        if not str(file_path.resolve()).startswith(str(adjusted_tb_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/adjustments/preview/{entity}/{filename}")
async def preview_adjustment_file(entity: str, filename: str, rows: int = 50):
    """Preview adjustment output file (first N rows)"""
    try:
        path_service = PathService(entity)

        # Security check - only allow previewing from adjusted_tb directory
        adjusted_tb_dir = path_service.get_adjusted_tb_dir(entity)
        file_path = adjusted_tb_dir / filename

        # Prevent directory traversal
        if not str(file_path.resolve()).startswith(str(adjusted_tb_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Read Excel file
        df = pd.read_excel(file_path)

        # Replace NaN and infinity values with None for JSON serialization
        df = df.replace([float('inf'), float('-inf')], None)
        df = df.where(pd.notnull(df), None)
        
        # Clean column names - replace NaN with empty string or index
        df.columns = [str(col) if pd.notna(col) else f"Column_{i}" for i, col in enumerate(df.columns)]

        # Limit rows
        preview_df = df.head(rows)

        # Convert to JSON-serializable format
        preview_data = preview_df.to_dict(orient='records')

        return {
            "filename": filename,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "preview_rows": len(preview_df),
            "data": preview_data,
            "summary": {
                "numeric_columns": df.select_dtypes(include=['float64', 'int64']).columns.tolist(),
                "text_columns": df.select_dtypes(include=['object']).columns.tolist(),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# Background processing function


async def run_adjustment_processing(processing_id: str, entity: str):
    """Run adjustment processing in background"""
    try:
        # Update status
        processing_status[processing_id].status = "processing"
        processing_status[processing_id].progress = 10
        processing_status[processing_id].message = "Initializing AI orchestrator..."
        
        print(f"🚀 Starting adjustment processing for {entity} (ID: {processing_id})")

        # Create AI service instance for this entity
        ai_service = AIOrchestratorService(entity)
        
        # Update status before starting
        processing_status[processing_id].progress = 15
        processing_status[processing_id].message = "Starting AI-powered adjustment processing..."

        # Run AI orchestrator with progress callback
        result = await ai_service.process_all_adjustments(
            entity, 
            processing_status=processing_status, 
            processing_id=processing_id
        )

        if result.get("success"):
            processing_status[processing_id].status = "completed"
            processing_status[processing_id].progress = 100
            processing_status[processing_id].message = "All adjustments processed successfully"
            processing_status[processing_id].result = result
            print(f"✅ Adjustment processing completed for {entity}")
        else:
            processing_status[processing_id].status = "failed"
            error_msg = result.get("error", "Processing failed")
            processing_status[processing_id].message = f"Failed: {error_msg}"
            processing_status[processing_id].result = result
            print(f"❌ Adjustment processing failed for {entity}: {error_msg}")
            if "stdout" in result:
                print(f"📋 STDOUT: {result['stdout'][:500]}...")  # Print first 500 chars
            if "stderr" in result:
                print(f"📋 STDERR: {result['stderr'][:500]}...")

    except Exception as e:
        processing_status[processing_id].status = "failed"
        processing_status[processing_id].message = f"Exception: {str(e)}"
        print(f"❌ Exception in adjustment processing for {entity}: {str(e)}")
        traceback.print_exc()

# Category Mapping


@app.post("/api/map-categories")
async def map_categories(entity: str = Form(...)):
    """Map GL codes to major/minor categories"""
    try:
        result = await mapping_service.map_categories(entity)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# Validation


@app.get("/api/validation/rules/{entity}")
async def get_validation_rules_config(entity: str):
    """Get validation rules configuration for an entity"""
    try:
        from backend.utils.tb_validate_7_rules import load_validation_rules_config

        # Normalize entity code
        entity = EntityConfig.normalize_entity_code(entity)

        # Load rules config
        rules_config = load_validation_rules_config(entity)

        # Format for frontend
        rules_list = []
        for rule_key, rule_data in rules_config.get('validation_rules', {}).items():
            rules_list.append({
                'rule_key': rule_key,
                'rule_number': rule_data.get('rule_number'),
                'rule_name': rule_data.get('rule_name'),
                'description': rule_data.get('description'),
                'enabled': rule_data.get('enabled', True),
                'category': rule_data.get('category'),
                'severity': rule_data.get('severity'),
                'notes': rule_data.get('notes')
            })

        # Sort by rule number
        rules_list.sort(key=lambda x: x['rule_number'])

        # Count enabled/disabled
        enabled_count = sum(1 for r in rules_list if r['enabled'])
        disabled_count = len(rules_list) - enabled_count

        return {
            'success': True,
            'entity': entity,
            'entity_name': rules_config.get('entity_name', entity),
            'rules': rules_list,
            'total_rules': len(rules_list),
            'enabled_rules': enabled_count,
            'disabled_rules': disabled_count,
            'tolerance_settings': rules_config.get('tolerance_settings', {}),
            'metadata': rules_config.get('metadata', {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/validate/6-rules")
async def validate_6_rules(
    entity: str = Form(...),
    rule_overrides: Optional[str] = Form(None)
):
    """Validate trial balance against enabled rules (dynamic per entity)

    Args:
        entity: Entity code
        rule_overrides: Optional JSON string with rule override settings
                       e.g., {"rule_1": true, "rule_2": false, ...}
    """
    try:
        # Parse rule overrides if provided
        overrides_dict = None
        if rule_overrides:
            try:
                overrides_dict = json.loads(rule_overrides)
                print(f"  📋 Rule overrides received: {overrides_dict}")
            except json.JSONDecodeError:
                print(f"  ⚠️ Invalid rule_overrides JSON: {rule_overrides}")

        result = await validation_service.validate_6_rules(entity, rule_overrides=overrides_dict)

        # If there are failed rules, return additional information
        if result.get('success') and result.get('rules_failed', 0) > 0:
            failed_details = await validation_service.get_failed_rules_details(entity)
            result['requires_acknowledgment'] = True
            result['failed_rules_details'] = failed_details.get('failed_rules', [])
        else:
            result['requires_acknowledgment'] = False

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/validate/failed-rules/{entity}")
async def get_failed_rules(entity: str):
    """Get detailed information about failed validation rules for acknowledgment"""
    try:
        result = await validation_service.get_failed_rules_details(entity)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/validate/acknowledgment-status/{entity}")
async def check_acknowledgment_status(entity: str):
    """Check if validation exceptions have been acknowledged"""
    try:
        status = await validation_service.check_acknowledgment_status(entity)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/validate/acknowledge-exceptions")
async def acknowledge_validation_exceptions(
    entity: str = Form(...),
    acknowledgment_note: str = Form(...),
    acknowledged_by: str = Form(...)
):
    """Acknowledge validation exceptions and allow proceeding to next step"""
    try:
        # Get failed rules details
        failed_details = await validation_service.get_failed_rules_details(entity)
        
        if not failed_details.get('has_failures'):
            return {
                "success": True,
                "message": "No validation failures found. You can proceed to the next step.",
                "requires_acknowledgment": False
            }
        
        # Create acknowledgment record
        acknowledgment = {
            "entity": entity,
            "acknowledged_by": acknowledged_by,
            "acknowledged_at": datetime.now().isoformat(),
            "acknowledgment_note": acknowledgment_note,
            "failed_rules": [
                {
                    "rule_number": rule['rule_number'],
                    "rule_name": rule['rule_name'],
                    "status": rule['status']
                }
                for rule in failed_details.get('failed_rules', [])
            ],
            "total_failed_rules": failed_details.get('failed_rules_count', 0)
        }
        
        # Save acknowledgment to a JSON file in the entity's output directory
        path_service = PathService()
        output_dir = path_service.get_adjusted_tb_dir(entity)
        acknowledgment_file = output_dir / "validation_acknowledgment.json"
        
        with open(acknowledgment_file, 'w') as f:
            json.dump(acknowledgment, f, indent=2)
        
        return {
            "success": True,
            "message": "Validation exceptions acknowledged. You can now proceed to the next step.",
            "acknowledgment": acknowledgment,
            "acknowledgment_file": str(acknowledgment_file),
            "can_proceed": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/validate/generate-insights")
async def generate_validation_insights(entity: str = Form(...)):
    """Generate AI-powered insights for validation failures"""
    try:
        from backend.utils.ai_validation_insights import generate_validation_insights
        
        success, message, report_path = generate_validation_insights(entity)
        
        if success:
            return {
                "success": True,
                "message": message,
                "report_path": report_path if report_path else None,
                "entity": entity,
                "has_failures": report_path is not None
            }
        else:
            # Check if it's a "file not found" type error
            if "not found" in message.lower() or "run step 5" in message.lower():
                raise HTTPException(
                    status_code=404, 
                    detail={
                        "error": "Validation report not found",
                        "message": message,
                        "entity": entity,
                        "suggestion": f"Please run Step 5 (6-Rules Validation) for entity '{entity.upper()}' first."
                    }
                )
            else:
                raise HTTPException(status_code=500, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "entity": entity
        }
        raise HTTPException(status_code=500, detail=error_detail) from e

# ============================================================================
# STEP 4: CATEGORY MAPPING ENDPOINTS
# ============================================================================


@app.post("/api/mapping/start/{entity}")
async def start_category_mapping(entity: str):
    """Start mapping GL codes to major/minor categories"""
    try:
        mapping_service = MappingService()

        # Check if mapping reference file exists
        reference_info = await mapping_service.get_mapping_reference(entity)

        if not reference_info.get('exists'):
            raise HTTPException(
                status_code=404,
                detail="Mapping reference file (glcode_major_minor_mappings.xlsx) not found. Please upload it first."
            )

        # Run the mapping
        result = await mapping_service.map_categories(entity)

        return {
            "success": result.get('success'),
            "message": result.get('message'),
            "entity": entity,
            "mapping_summary": {
                "total_records": result.get(
                    'total_records',
                    0),
                "mapped_records": result.get(
                    'mapped_records',
                    0),
                "unmapped_records": result.get(
                    'unmapped_records',
                    0),
                "mapping_percentage": round(
                    (result.get(
                        'mapped_records',
                        0) /
                     result.get(
                        'total_records',
                        1)) *
                    100,
                    2) if result.get(
                    'total_records',
                    0) > 0 else 0},
            "output_file": result.get('output_path'),
            "download_url": f"/api/mapping/download/{entity}/final_trialbalance.xlsx" if result.get('success') else None,
            "next_step": {
                "available": result.get('success'),
                "next_step": "validate_6_rules",
                "next_step_label": "Step 5: Validate 6 Rules",
                "next_step_description": "Validate the mapped trial balance against 6 accounting rules",
                "next_step_url": f"/api/validation/6rules/{entity}" if result.get('success') else None}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/mapping/reference/{entity}")
async def get_mapping_reference(entity: str):
    """Get mapping reference file information"""
    try:
        mapping_service = MappingService()
        result = await mapping_service.get_mapping_reference(entity)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/mapping/download/{entity}/{filename}")
async def download_mapping_file(entity: str, filename: str):
    """Download mapped trial balance file"""
    try:
        path_service = PathService(entity)

        # Get the output directory
        output_dir = path_service.get_adjusted_tb_dir(entity)
        file_path = output_dir / filename

        # Security check
        if not str(file_path.resolve()).startswith(str(output_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# ============================================================================
# AI INSIGHTS
# ============================================================================

# AI Insights


@app.post("/api/ai/insights")
async def generate_ai_insights(request: dict):
    """Generate AI insights for validation results"""
    try:
        validation_result = request.get('validation_result', {})
        entity = request.get('entity', 'cpm')

        print(f"🤖 Generating AI insights for entity: {entity}")
        print(f"   Validation result keys: {list(validation_result.keys())}")

        # Create AI service instance for this entity
        ai_service = AIOrchestratorService(entity)
        insights = await ai_service.get_ai_insights(validation_result)

        print("✅ AI insights generated successfully")

        # Save insights to file
        path_service = PathService(entity)
        output_dir = path_service.get_adjusted_tb_dir(entity)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save insights as text file
        insights_file = output_dir / \
            f"AI_Insights_{entity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(insights_file, 'w', encoding='utf-8') as f:
            f.write(insights)

        print(f"✅ AI insights saved to: {insights_file}")

        return {
            "insights": insights,
            "file_path": str(insights_file)
        }
    except Exception as e:
        print(f"❌ Error generating AI insights: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

# Feedback


@app.post("/api/feedback")
async def submit_feedback(request: dict):
    """Submit user feedback"""
    try:
        # For now, just log the feedback
        # In production, you'd save this to a database
        logging.info("Feedback received: %s", request)
        return {
            "success": True,
            "message": "Feedback submitted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# File Download


@app.get("/api/download/{file_type}")
async def download_output_file(file_type: str, entity: str):
    """Download processed files"""
    try:
        file_path = file_service.get_output_file_path(file_type, entity)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# Financial Statement Generation (Legacy)


@app.post("/api/generate/notes")
async def generate_notes(
    entity: str = Form(...),
    note_types: List[str] = Form(...)
):
    """Generate financial notes (Legacy)"""
    try:
        # Create AI service instance for this entity
        ai_service = AIOrchestratorService(entity)
        result = await ai_service.generate_notes(entity, note_types)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/generate/statements")
async def generate_statements(
    entity: str = Form(...),
    statement_types: List[str] = Form(...)
):
    """Generate financial statements (Legacy)"""
    try:
        # Create AI service instance for this entity
        ai_service = AIOrchestratorService(entity)
        result = await ai_service.generate_statements(entity, statement_types)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# New Financial Statements Endpoints


@app.post("/api/statements/profit-loss")
async def generate_profit_loss_statement(
    entity: str = Form(...),
    period_ended: Optional[str] = Form(None),
    note_numbers: Optional[List[str]] = Form(None)
):
    """Generate Profit & Loss Statement"""
    try:
        result = FinancialStatementService.generate_profit_loss(
            entity, period_ended, note_numbers)
        if result.get("success"):
            return result

        raise HTTPException(
            status_code=400, detail=result.get(
                "error", "Generation failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/statements/balance-sheet")
async def generate_balance_sheet_statement(
    entity: str = Form(...),
    as_at_date: Optional[str] = Form(None),
    note_numbers: Optional[List[str]] = Form(None)
):
    """Generate Balance Sheet"""
    try:
        result = FinancialStatementService.generate_balance_sheet(
            entity, as_at_date, note_numbers)
        if result.get("success"):
            return result

        raise HTTPException(
            status_code=400, detail=result.get(
                "error", "Generation failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/statements/cash-flow")
async def generate_cash_flow_statement(
    entity: str = Form(...),
    period_ended: Optional[str] = Form(None),
    note_numbers: Optional[List[str]] = Form(None)
):
    """Generate Cash Flow Statement"""
    try:
        result = FinancialStatementService.generate_cash_flow(
            entity, period_ended, note_numbers)
        if result.get("success"):
            return result

        raise HTTPException(
            status_code=400, detail=result.get(
                "error", "Generation failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/statements/generate-all")
async def generate_all_statements(
    entity: str = Form(...),
    period_ended: Optional[str] = Form(None),
    as_at_date: Optional[str] = Form(None)
):
    """Generate all financial statements (P&L, Balance Sheet, Cash Flow)"""
    try:
        # Check if validation exceptions have been acknowledged
        ack_status = await validation_service.check_acknowledgment_status(entity)
        
        if not ack_status.get('can_proceed', True):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation acknowledgment required",
                    "message": ack_status.get('message'),
                    "has_failures": ack_status.get('has_failures'),
                    "failed_rules_count": ack_status.get('failed_rules_count', 0),
                    "action_required": "Please acknowledge validation exceptions before generating financial statements"
                }
            )
        
        result = FinancialStatementService.generate_all_statements(
            entity, period_ended, as_at_date)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/upload/notes-trial-balance")
async def upload_notes_trial_balance(
    entity: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload trial balance CSV file for note generation"""
    try:
        # Normalize entity name using centralized config
        entity = EntityConfig.normalize_entity_code(entity)

        print("\n📤 Upload notes trial balance CSV request:")
        print(f"   Entity: {entity}")
        print(f"   Filename: {file.filename}")
        print(f"   Content-Type: {file.content_type}")

        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files (.csv) are allowed for notes trial balance"
            )

        # Ensure entity directory structure exists
        path_service = PathService(entity)
        path_service.create_entity_structure(entity)
        
        # Get notes trial balance directory
        notes_tb_dir = path_service.get_notes_trialbalance_dir(entity)
        notes_tb_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Notes TB directory verified: {notes_tb_dir}")

        # Save file to notes-input/Trialbalance directory
        file_path = notes_tb_dir / file.filename
        
        print(f"   Target file: {file_path}")
        
        # If file exists, remove it first to ensure clean overwrite
        if file_path.exists():
            print("   Removing existing file...")
            file_path.unlink()

        # Save file
        try:
            contents = await file.read()
            with open(file_path, 'wb') as f:
                f.write(contents)
            print(f"   ✅ Written {len(contents)} bytes")
        except Exception as e:
            print(f"   ❌ Error writing file: {str(e)}")
            raise

        return {
            "success": True,
            "message": "Notes trial balance CSV uploaded successfully",
            "file_path": str(file_path),
            "filename": file.filename,
            "entity": entity,
            "folder": "notes-input/Trialbalance",
            "size_bytes": len(contents)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Error uploading notes trial balance: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload notes trial balance: {str(e)}"
        ) from e


@app.get("/api/notes-trial-balance/{entity}")
async def get_notes_trial_balance_info(entity: str):
    """Get information about the notes trial balance CSV file"""
    try:
        # Normalize entity name
        entity = EntityConfig.normalize_entity_code(entity)
        
        path_service = PathService(entity)
        notes_tb_dir = path_service.get_notes_trialbalance_dir(entity)
        
        if not notes_tb_dir.exists():
            return {
                "exists": False,
                "message": "Notes trial balance directory not found",
                "expected_path": str(notes_tb_dir)
            }
        
        # Find CSV files
        csv_files = list(notes_tb_dir.glob("*.csv"))
        
        if not csv_files:
            return {
                "exists": False,
                "message": "No CSV files found in notes trial balance directory",
                "directory": str(notes_tb_dir)
            }
        
        # Get info about the first CSV file found
        csv_file = csv_files[0]
        file_stat = csv_file.stat()
        
        # Read first few rows to get column info
        try:
            import pandas as pd
            df = pd.read_csv(csv_file, nrows=5)
            columns = df.columns.tolist()
            sample_data = df.head(3).to_dict('records')
        except Exception:
            columns = []
            sample_data = []
        
        return {
            "exists": True,
            "filename": csv_file.name,
            "file_path": str(csv_file),
            "size_bytes": file_stat.st_size,
            "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "columns": columns,
            "sample_data": sample_data,
            "total_csv_files": len(csv_files),
            "download_url": f"/api/notes-trial-balance/download/{entity}/{csv_file.name}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/notes-trial-balance/download/{entity}/{filename}")
async def download_notes_trial_balance(entity: str, filename: str):
    """Download notes trial balance CSV file"""
    try:
        # Normalize entity name
        entity = EntityConfig.normalize_entity_code(entity)
        
        path_service = PathService(entity)
        notes_tb_dir = path_service.get_notes_trialbalance_dir(entity)
        file_path = notes_tb_dir / filename
        
        # Security check - prevent directory traversal
        if not str(file_path.resolve()).startswith(str(notes_tb_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='text/csv'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        reload_excludes=["debug_*.py", "*.log", "*.tmp", "data/**", "reports/**", "logs/**"],
    )
