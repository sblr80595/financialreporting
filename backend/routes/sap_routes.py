"""
SAP Integration Routes
======================
Handles SAP connectivity checks and data extraction for trial balances
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.sap_connect.connectivity_manager import ConnectivityManager
from backend.sap_connect.data_extractor import DataExtractor
from backend.services.path_service import PathService

router = APIRouter()

# Entity mapping: Frontend entity code -> SAP entity ID
# This maps the entities used in the frontend to those defined in entities.json
ENTITY_SAP_MAPPING = {
    "cpm": "CPM_CHEMOPHARM",  # SQL Server connection to Chemopharm Malaysia
    "analisa_resource": None,
    "neoscience_sdn": None,
    "lifeline_holdings": None,
    "lifeline_diagnostics": None,
    # Add SAP mappings when available, e.g.:
    # "transhealth": "THL",
    # "translumina": "TTL",
    # "integris": "IHL"
}


class SAPConnectivityResponse(BaseModel):
    """Response for SAP connectivity check"""
    available: bool
    sap_entity_id: Optional[str]
    entity_name: Optional[str]
    connection_type: Optional[str]
    message: str
    status: Optional[str] = None
    response_time: Optional[float] = None


class SAPExtractionRequest(BaseModel):
    """Request for SAP trial balance extraction"""
    entity: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class SAPExtractionResponse(BaseModel):
    """Response for SAP trial balance extraction"""
    success: bool
    message: str
    file_path: Optional[str] = None
    filename: Optional[str] = None
    rows_extracted: Optional[int] = None
    extraction_time: Optional[str] = None


@router.get("/sap/check-connectivity/{entity}", response_model=SAPConnectivityResponse)
async def check_sap_connectivity(entity: str):
    """
    Check if SAP connectivity is available for the given entity
    
    Args:
        entity: Frontend entity code (e.g., "cpm", "analisa_resource")
        
    Returns:
        Connectivity status and details
    """
    try:
        # Check if entity has SAP mapping
        sap_entity_id = ENTITY_SAP_MAPPING.get(entity.lower())
        
        if not sap_entity_id:
            return SAPConnectivityResponse(
                available=False,
                sap_entity_id=None,
                entity_name=None,
                connection_type=None,
                message="Work in Progress - SAP integration not yet configured for this entity"
            )
        
        # Initialize connectivity manager
        conn_mgr = ConnectivityManager()
        
        # Get entity configuration from SAP config
        sap_entity = conn_mgr.get_entity_by_id(sap_entity_id)
        
        if not sap_entity:
            return SAPConnectivityResponse(
                available=False,
                sap_entity_id=sap_entity_id,
                entity_name=None,
                connection_type=None,
                message=f"SAP entity configuration not found for ID: {sap_entity_id}"
            )
        
        # Test connection based on type
        connection_type = sap_entity.get("connection_type", "unknown")
        
        if connection_type == "api":
            success, msg, response_time = conn_mgr.test_api_connection(sap_entity)
        elif connection_type == "sql":
            success, msg, response_time = conn_mgr.test_sql_connection(sap_entity)
        else:
            return SAPConnectivityResponse(
                available=False,
                sap_entity_id=sap_entity_id,
                entity_name=sap_entity.get("name"),
                connection_type=connection_type,
                message=f"Unknown connection type: {connection_type}"
            )
        
        return SAPConnectivityResponse(
            available=success,
            sap_entity_id=sap_entity_id,
            entity_name=sap_entity.get("name"),
            connection_type=connection_type,
            message=msg,
            status="online" if success else "offline",
            response_time=response_time
        )
        
    except Exception as e:
        return SAPConnectivityResponse(
            available=False,
            sap_entity_id=None,
            entity_name=None,
            connection_type=None,
            message=f"Error checking connectivity: {str(e)}"
        )


@router.post("/sap/extract-trial-balance", response_model=SAPExtractionResponse)
async def extract_trial_balance_from_sap(request: SAPExtractionRequest):
    """
    Extract trial balance data from SAP for the given entity
    
    Args:
        request: Entity and optional date range
        
    Returns:
        Extraction status and file path
    """
    try:
        entity = request.entity.lower()
        
        # Check if entity has SAP mapping
        sap_entity_id = ENTITY_SAP_MAPPING.get(entity)
        
        if not sap_entity_id:
            raise HTTPException(
                status_code=400,
                detail="SAP integration not configured for this entity"
            )
        
        # Initialize managers
        conn_mgr = ConnectivityManager()
        data_extractor = DataExtractor(conn_mgr)
        
        # Get entity configuration
        sap_entity = conn_mgr.get_entity_by_id(sap_entity_id)
        
        if not sap_entity:
            raise HTTPException(
                status_code=404,
                detail=f"SAP entity configuration not found for ID: {sap_entity_id}"
            )
        
        # Determine date range (default to current financial year if not provided)
        if not request.start_date or not request.end_date:
            # Default to Apr 2024 - Mar 2025 (adjust as needed)
            start_date = "2024-04-01"
            end_date = "2025-03-31"
        else:
            start_date = request.start_date
            end_date = request.end_date
        
        print(f"\n📊 Extracting trial balance from SAP:")
        print(f"   Entity: {entity} -> {sap_entity_id}")
        print(f"   Period: {start_date} to {end_date}")
        
        # Extract trial balance
        extraction_start = datetime.now()
        df = data_extractor.extract_trial_balance(sap_entity_id, start_date, end_date)
        extraction_time = (datetime.now() - extraction_start).total_seconds()
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="No trial balance data found for the specified period"
            )
        
        print(f"   ✅ Extracted {len(df)} rows in {extraction_time:.2f}s")
        
        # Ensure entity directory exists
        path_service = PathService(entity)
        path_service.create_entity_structure(entity)
        
        # Save to entity's unadjusted trial balance folder as sap_unadjusted_trialbalance.xlsx
        entity_input_dir = path_service.get_unadjusted_tb_dir(entity)
        filename = "sap_unadjusted_trialbalance.xlsx"
        file_path = entity_input_dir / filename
        
        # Save to Excel
        df.to_excel(file_path, index=False, sheet_name="Trial Balance")
        
        print(f"   ✅ Saved to: {file_path}")
        
        return SAPExtractionResponse(
            success=True,
            message=f"Successfully extracted trial balance from SAP",
            file_path=str(file_path),
            filename=filename,
            rows_extracted=len(df),
            extraction_time=f"{extraction_time:.2f}s"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Error extracting trial balance: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract trial balance: {str(e)}"
        )


@router.get("/sap/entities")
async def get_sap_entities():
    """
    Get list of all available SAP entities and their mapping status
    
    Returns:
        List of entities with SAP availability
    """
    try:
        conn_mgr = ConnectivityManager()
        all_sap_entities = conn_mgr.get_all_entities()
        
        # Create mapping info
        entities_info = []
        for frontend_entity, sap_id in ENTITY_SAP_MAPPING.items():
            entity_info = {
                "frontend_code": frontend_entity,
                "sap_entity_id": sap_id,
                "sap_available": sap_id is not None
            }
            
            if sap_id:
                sap_entity = conn_mgr.get_entity_by_id(sap_id)
                if sap_entity:
                    entity_info["sap_name"] = sap_entity.get("name")
                    entity_info["connection_type"] = sap_entity.get("connection_type")
                    entity_info["status"] = sap_entity.get("status", "active")
            
            entities_info.append(entity_info)
        
        return {
            "entities": entities_info,
            "total_sap_entities": len(all_sap_entities),
            "mapped_entities": sum(1 for e in entities_info if e["sap_available"])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get SAP entities: {str(e)}"
        )
