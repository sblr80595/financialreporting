"""
File management service for handling uploads and downloads
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .path_service import PathService


class FileService:
    """Service for managing file operations"""

    def __init__(self, entity: str = None):
        """
        Initialize FileService

        Args:
            entity: Entity code (e.g., 'cpm', 'hausen')
        """
        self.path_service = PathService(entity)
        self.entity = entity

    def set_entity(self, entity: str):
        """Set the current entity"""
        self.entity = entity
        self.path_service.set_entity(entity)
        # Ensure entity structure exists
        self.path_service.create_entity_structure(entity)

    async def save_trial_balance(self, file, entity: str) -> str:
        """Save uploaded trial balance file (overwrites if exists)"""
        self.set_entity(entity)

        # Use original filename or generate one
        filename = file.filename if hasattr(
            file, 'filename') else f"{entity}_trial_balance_sap.xlsx"
        tb_dir = self.path_service.get_unadjusted_tb_dir(entity)
        file_path = tb_dir / filename

        # Ensure directory exists
        tb_dir.mkdir(parents=True, exist_ok=True)

        print(f"      Target directory: {tb_dir}")
        print(f"      Target file: {file_path}")
        print(f"      File exists: {file_path.exists()}")

        # If file exists, remove it first to ensure clean overwrite
        if file_path.exists():
            print("      Removing existing file...")
            file_path.unlink()

        # Save file (overwrite mode)
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            print(f"      Written {len(content)} bytes")
        except Exception as e:
            print(f"      ❌ Error writing file: {str(e)}")
            raise

        return str(file_path)

    async def save_adjustment_file(self, file, entity: str) -> str:
        """Save uploaded adjustment file"""
        self.set_entity(entity)

        # Keep original filename
        filename = file.filename if hasattr(file, 'filename') else file
        file_path = self.path_service.get_manual_adjustments_dir(entity) / filename

        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return str(file_path)

    async def save_mapping_file(self, file, entity: str) -> str:
        """Save GL code mapping file"""
        self.set_entity(entity)

        filename = file.filename if hasattr(
            file, 'filename') else "glcode_major_minor_mappings.xlsx"
        file_path = self.path_service.get_unadjusted_tb_dir(entity) / filename

        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return str(file_path)

    async def save_adjustment_config(self, file, entity: str) -> str:
        """Save adjustment configuration file"""
        self.set_entity(entity)

        filename = file.filename if hasattr(
            file, 'filename') else "adjusted_trial_balance_config.xlsx"
        file_path = self.path_service.get_manual_adjustments_dir(entity) / filename

        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return str(file_path)

    def get_output_file_path(self, file_type: str, entity: str) -> str:
        """Get path to output file"""
        self.set_entity(entity)
        file_mapping = {
            "adjusted_trial_balance": self.path_service.get_adjusted_tb_path(entity),
            "final_trial_balance": self.path_service.get_final_tb_path(entity),
            "validation_report": self.path_service.get_validation_report_path(entity)
        }
        # Note: Individual reconciliation files are no longer generated
        # The system now creates only the final adjusted_trialbalance.xlsx directly

        file_path = file_mapping.get(file_type)
        if file_path:
            return str(file_path)

        # Default: return path in adjusted-trialbalance directory
        return str(self.path_service.get_adjusted_tb_dir(entity) / f"{file_type}.xlsx")

    def _get_file_metadata(self, folder_path: Path, filename: str) -> Dict[str, Any]:
        """Get metadata for a file"""
        file_path = folder_path / filename
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            return {
                "filename": filename,
                "file_size": int(stat.st_size) if stat.st_size is not None else 0,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat() if stat.st_ctime else None,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat() if stat.st_mtime else None
            }
        except Exception as e:
            print(f"Warning: Error getting metadata for {filename}: {e}")
            return {
                "filename": filename,
                "file_size": 0,
                "created_at": None,
                "modified_at": None
            }

    def list_available_files(self, entity: str) -> Dict[str, List[Dict[str, Any]]]:
        """List available files for an entity with metadata"""
        self.set_entity(entity)

        def get_files_with_metadata(folder_path: Path) -> List[Dict[str, Any]]:
            """Helper to get files with metadata from a folder"""
            filenames = self.path_service.list_files_in_folder(folder_path)
            files = []
            for filename in filenames:
                metadata = self._get_file_metadata(folder_path, filename)
                if metadata:
                    files.append(metadata)
            return files

        return {
            "config": get_files_with_metadata(
                self.path_service.get_config_dir(entity)
            ),
            "unadjusted_trialbalance": get_files_with_metadata(
                self.path_service.get_unadjusted_tb_dir(entity)
            ),
            "manual_adjustments": get_files_with_metadata(
                self.path_service.get_manual_adjustments_dir(entity)
            ),
            "pre_adjusted_trialbalance": get_files_with_metadata(
                self.path_service.get_pre_adjusted_tb_dir(entity)
            ),
            "adjusted_trialbalance": get_files_with_metadata(
                self.path_service.get_adjusted_tb_dir(entity)
            ),
            "generated_notes": get_files_with_metadata(
                self.path_service.get_generated_notes_dir(entity)
            ),
            "financial_statements": get_files_with_metadata(
                self.path_service.get_financial_statements_dir(entity)
            )
        }

    def get_file_path(self, filename: str, folder_type: str, entity: str) -> str:
        """
        Get full file path for a file

        Args:
            filename: Name of the file
            folder_type: Type of folder
            entity: Entity code

        Returns:
            Full file path
        """
        self.set_entity(entity)

        folder_map = {
            "config": self.path_service.get_config_dir(entity),
            "unadjusted_trialbalance": self.path_service.get_unadjusted_tb_dir(entity),
            "manual_adjustments": self.path_service.get_manual_adjustments_dir(entity),
            "pre_adjusted_trialbalance": self.path_service.get_pre_adjusted_tb_dir(entity),
            "adjusted_trialbalance": self.path_service.get_adjusted_tb_dir(entity),
            "generated_notes": self.path_service.get_generated_notes_dir(entity),
            "financial_statements": self.path_service.get_financial_statements_dir(entity),
        }

        folder = folder_map.get(folder_type)
        if not folder:
            raise ValueError(f"Invalid folder type: {folder_type}")

        return str(folder / filename)

    def check_file_exists(self, filename: str, folder_type: str, entity: str) -> Dict[str, Any]:
        """
        Check if a file exists and return information

        Args:
            file_path: Filename to check
            folder_type: Type of folder (unadjusted_tb, manual_adjustments, etc.)
            entity: Entity code

        Returns:
            Dict with file existence and info
        """
        self.set_entity(entity)

        # Support both legacy and current folder type keys
        folder_map = {
            # Current keys used by API/UI
            "unadjusted_trialbalance": self.path_service.get_unadjusted_tb_dir(entity),
            "manual_adjustments": self.path_service.get_manual_adjustments_dir(entity),
            "pre_adjusted_trialbalance": self.path_service.get_pre_adjusted_tb_dir(entity),
            "adjusted_trialbalance": self.path_service.get_adjusted_tb_dir(entity),
            "generated_notes": self.path_service.get_generated_notes_dir(entity),
            "financial_statements": self.path_service.get_financial_statements_dir(entity),
            # Legacy aliases kept for backward compatibility
            "unadjusted_tb": self.path_service.get_unadjusted_tb_dir(entity),
            "pre_adjusted_tb": self.path_service.get_pre_adjusted_tb_dir(entity),
            "adjusted_tb": self.path_service.get_adjusted_tb_dir(entity),
        }

        folder = folder_map.get(folder_type)
        if not folder:
            return {"exists": False, "error": "Invalid folder type"}

        full_path = folder / filename
        return self.get_file_info(str(full_path))

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        path = Path(file_path)
        if not path.exists():
            return {"exists": False, "filename": path.name}

        stat = path.stat()
        return {
            "filename": path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "exists": True,
            "path": str(path)
        }

    def delete_file(self, file_path: str, folder_type: str, entity: str) -> bool:
        """
        Delete a file

        Args:
            file_path: Filename to delete
            folder_type: Type of folder
            entity: Entity code

        Returns:
            True if deleted successfully
        """
        # Make delete idempotent from UI point of view:
        # - If file exists, delete it.
        # - If it doesn't exist, still return True so UI can clean up state.
        file_info = self.check_file_exists(file_path, folder_type, entity)
        if file_info.get("exists"):
            Path(file_info["path"]).unlink()
            return True
        # If folder_type was invalid previously, try resolving via get_file_path
        try:
            resolved_path = Path(self.get_file_path(file_path, folder_type, entity))
            if resolved_path.exists():
                resolved_path.unlink()
        except Exception:
            # Ignore resolution errors and treat as already deleted
            pass
        return True

    def cleanup_old_files(self, entity: str, max_age_hours: int = 24):
        """Clean up old files for an entity"""
        self.set_entity(entity)
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        # Clean all entity folders
        folders = [
            self.path_service.get_unadjusted_tb_dir(entity),
            self.path_service.get_manual_adjustments_dir(entity),
            self.path_service.get_adjusted_tb_dir(entity),
        ]

        for folder in folders:
            if not folder.exists():
                continue
            for file_path in folder.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()

    def get_available_entities(self) -> List[str]:
        """Get list of available entities"""
        return self.path_service.get_available_entities()
