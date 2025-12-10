"""
Utility Module for Entity-based Path Management in Utils Scripts
"""

import sys
import os
from pathlib import Path

# Import PathService from the services directory
from backend.services.path_service import PathService


def get_entity_paths(entity: str):
    """
    Get all relevant paths for an entity
    
    Args:
        entity: Entity code (e.g., 'cpm', 'hausen')
        
    Returns:
        Dictionary with all path information
    """
    path_service = PathService(entity)
    path_service.create_entity_structure(entity)
    
    return {
        # Input paths
        "trial_balance_file": path_service.get_trial_balance_path(entity),
        "unadjusted_tb_dir": path_service.get_unadjusted_tb_dir(entity),
        "manual_adjustments_dir": path_service.get_manual_adjustments_dir(entity),
        "adjustment_config_file": path_service.get_adjustment_config_path(entity),
        "mapping_file": path_service.get_mapping_file_path(entity),
        
        # Output paths
        "adjusted_tb_file": path_service.get_adjusted_tb_path(entity),
        "final_tb_file": path_service.get_final_tb_path(entity),
        "validation_report": path_service.get_validation_report_path(entity),
        "adjusted_tb_dir": path_service.get_adjusted_tb_dir(entity),
        "generated_notes_dir": path_service.get_generated_notes_dir(entity),
        "financial_statements_dir": path_service.get_financial_statements_dir(entity),
    }


def setup_entity_folders(entity: str):
    """
    Ensure all folders exist for an entity
    
    Args:
        entity: Entity code
    """
    path_service = PathService(entity)
    folders = path_service.create_entity_structure(entity)
    print(f"✅ Entity folder structure created for: {entity}")
    for folder_type, path in folders.items():
        print(f"  - {folder_type}: {path}")
    return folders
