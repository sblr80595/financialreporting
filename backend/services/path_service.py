"""
Path Management Service - Centralized path configuration for entity-based folder structure
"""

from pathlib import Path
from typing import Dict, List, Optional

from backend.config.settings import settings


# Resolve project root (repo root) to ensure consistent relative paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# DATA_DIR can be absolute (via env) or relative; normalize to absolute path
_configured_data_dir = settings.DATA_DIR
if not _configured_data_dir.is_absolute():
    DATA_ROOT_PATH = (PROJECT_ROOT / _configured_data_dir).resolve()
else:
    DATA_ROOT_PATH = _configured_data_dir.resolve()


class PathService:
    """
    Manages all file paths in the application using entity-based structure.

    Folder Structure:
    data/
      └── {entity}/
          ├── input/
          │   ├── config/
          │   ├── unadjusted-trialbalance/
          │   ├── manual-adjustments/
          │   ├── pre-adjusted-trialbalance/
          │   └── notes-input/
          │       └── Trialbalance/
          └── output/
              ├── adjusted-trialbalance/
              ├── generated_notes/
              └── financial_statements/
    """

    # Root data directory (absolute path)
    DATA_ROOT = DATA_ROOT_PATH

    # Input subdirectories
    INPUT_CONFIG = "config"
    INPUT_UNADJUSTED_TB = "unadjusted-trialbalance"
    INPUT_MANUAL_ADJUSTMENTS = "manual-adjustments"
    INPUT_PRE_ADJUSTED_TB = "pre-adjusted-trialbalance"
    INPUT_NOTES_INPUT = "notes-input"

    # Output subdirectories
    OUTPUT_ADJUSTED_TB = "adjusted-trialbalance"
    OUTPUT_GENERATED_NOTES = "generated_notes"
    OUTPUT_FINANCIAL_STATEMENTS = "financial_statements"

    def __init__(self, entity: str = None):
        """
        Initialize PathService for a specific entity

        Args:
            entity: Entity code (e.g., 'cpm', 'hausen', 'integris')
        """
        self.entity = entity.lower() if entity else None

    def set_entity(self, entity: str):
        """Set the current entity"""
        self.entity = entity.lower()

    @staticmethod
    def get_all_entities() -> List[str]:
        """
        Get list of all entities from the configured entity list.
        
        Note: This now uses the configured entity list from backend/config/entities.py
        instead of auto-discovering from the data directory to maintain control
        over which entities are visible to users.

        Returns:
            List of entity codes (e.g., ['cpm', 'analisa_resource', 'neoscience_sdn'])
        """
        # Import here to avoid circular dependency
        from backend.config.entities import EntityConfig
        
        # Return only configured entities
        configured_entities = EntityConfig.get_all_entities()
        entity_codes = [entity['code'] for entity in configured_entities]
        
        return sorted(entity_codes)
        
        # OLD AUTO-DISCOVERY CODE (commented out):
        # entities = []
        # data_root = PathService.DATA_ROOT
        #
        # if data_root.exists():
        #     for item in data_root.iterdir():
        #         # Skip hidden files, non-directories, and specific excluded patterns
        #         if (item.is_dir() and
        #             not item.name.startswith('.') and
        #                 item.name not in ['__pycache__', 'backend.main:app']):
        #             entities.append(item.name.lower())
        #
        # return sorted(entities)

    def get_entity_root(self, entity: str = None) -> Path:
        """Get the root directory for an entity"""
        entity = (entity or self.entity).lower()
        return self.DATA_ROOT / entity

    def get_input_dir(self, entity: str = None) -> Path:
        """Get the input directory for an entity"""
        return self.get_entity_root(entity) / "input"

    def get_output_dir(self, entity: str = None) -> Path:
        """Get the output directory for an entity"""
        return self.get_entity_root(entity) / "output"

    # Input folder paths
    def get_config_dir(self, entity: str = None) -> Path:
        """Get the config directory"""
        return self.get_input_dir(entity) / self.INPUT_CONFIG

    def get_unadjusted_tb_dir(self, entity: str = None) -> Path:
        """Get the unadjusted trial balance directory"""
        return self.get_input_dir(entity) / self.INPUT_UNADJUSTED_TB

    def get_manual_adjustments_dir(self, entity: str = None) -> Path:
        """Get the manual adjustments directory"""
        return self.get_input_dir(entity) / self.INPUT_MANUAL_ADJUSTMENTS

    def get_pre_adjusted_tb_dir(self, entity: str = None) -> Path:
        """Get the pre-adjusted trial balance directory"""
        return self.get_input_dir(entity) / self.INPUT_PRE_ADJUSTED_TB

    def get_notes_input_dir(self, entity: str = None) -> Path:
        """Get the notes input directory"""
        return self.get_input_dir(entity) / self.INPUT_NOTES_INPUT

    def get_notes_trialbalance_dir(self, entity: str = None) -> Path:
        """Get the notes input trial balance directory"""
        return self.get_notes_input_dir(entity) / "Trialbalance"

    # Output folder paths
    def get_adjusted_tb_dir(self, entity: str = None) -> Path:
        """Get the adjusted trial balance directory"""
        return self.get_output_dir(entity) / self.OUTPUT_ADJUSTED_TB

    def get_generated_notes_dir(self, entity: str = None) -> Path:
        """Get the generated notes directory"""
        return self.get_output_dir(entity) / self.OUTPUT_GENERATED_NOTES

    def get_financial_statements_dir(self, entity: str = None) -> Path:
        """Get the financial statements directory"""
        return self.get_output_dir(entity) / self.OUTPUT_FINANCIAL_STATEMENTS

    # Specific file paths
    def get_trial_balance_path(self, entity: str = None, filename: str = None) -> Path:
        """Get path for trial balance file"""
        entity = (entity or self.entity).lower()
        if filename is None:
            filename = f"{entity}_trial_balance_sap.xlsx"
        return self.get_unadjusted_tb_dir(entity) / filename

    def find_trial_balance_file(self, entity: str = None) -> Optional[Path]:
        """
        Find the trial balance file in the unadjusted TB directory.
        Searches for common naming patterns like:
        - unadjusted_trialbalance.xlsx
        - {entity}_trial_balance_sap.xlsx
        - trial_balance.xlsx
        - Any .xlsx or .xls file containing 'trial' or 'balance'

        Returns:
            Path to the trial balance file or None if not found
        """
        entity = (entity or self.entity).lower()
        tb_dir = self.get_unadjusted_tb_dir(entity)

        if not tb_dir.exists():
            return None

        # Search patterns in order of preference
        patterns = [
            "unadjusted_trialbalance.xlsx",
            "unadjusted_trialbalance.xls",
            f"{entity}_trial_balance_sap.xlsx",
            f"{entity}_trial_balance_sap.xls",
            "trial_balance.xlsx",
            "trial_balance.xls",
        ]

        # Try exact matches first
        for pattern in patterns:
            file_path = tb_dir / pattern
            if file_path.exists():
                return file_path

        # Fallback: search for any Excel file containing 'trial' or 'balance' (case-insensitive)
        for ext in ['*.xlsx', '*.xls']:
            for file_path in tb_dir.glob(ext):
                filename_lower = file_path.name.lower()
                if 'trial' in filename_lower or 'balance' in filename_lower:
                    return file_path

        # Last resort: return first Excel file
        excel_files = list(tb_dir.glob('*.xlsx')) + list(tb_dir.glob('*.xls'))
        if excel_files:
            return excel_files[0]

        return None

    def get_adjustment_file_path(self, filename: str, entity: str = None) -> Path:
        """Get path for adjustment file"""
        return self.get_manual_adjustments_dir(entity) / filename

    def get_adjusted_tb_path(
            self,
            entity: str = None,
            filename: str = "adjusted_trialbalance.xlsx") -> Path:
        """Get path for adjusted trial balance file"""
        return self.get_adjusted_tb_dir(entity) / filename

    def get_final_tb_path(
            self,
            entity: str = None,
            filename: str = "final_trialbalance.xlsx") -> Path:
        """Get path for final trial balance file"""
        return self.get_adjusted_tb_dir(entity) / filename

    def get_validation_report_path(
            self,
            entity: str = None,
            filename: str = "trialbalance_6rule_validation_report.xlsx") -> Path:
        """Get path for validation report"""
        return self.get_adjusted_tb_dir(entity) / filename

    def get_mapping_file_path(
            self,
            entity: str = None,
            filename: str = "glcode_major_minor_mappings.xlsx") -> Path:
        """Get path for GL code mapping file"""
        return self.get_config_dir(entity) / filename

    def get_adjustment_config_path(
            self,
            entity: str = None,
            filename: str = "adjusted_trial_balance_config.xlsx") -> Path:
        """Get path for adjustment configuration file"""
        return self.get_config_dir(entity) / filename

    def get_note_path(self, note_name: str, entity: str = None) -> Path:
        """Get path for generated note file"""
        return self.get_generated_notes_dir(entity) / f"{note_name}.md"

    def get_statement_path(self, statement_type: str, entity: str = None) -> Path:
        """Get path for financial statement file"""
        entity = (entity or self.entity).lower()
        filename = f"{entity}_{statement_type}.xlsx"
        return self.get_financial_statements_dir(entity) / filename

    # Directory management
    def create_entity_structure(self, entity: str = None) -> Dict[str, Path]:
        """
        Create complete folder structure for an entity

        Returns:
            Dictionary mapping folder types to their paths
        """
        entity = (entity or self.entity).lower()

        folders = {
            "entity_root": self.get_entity_root(entity),
            "input": self.get_input_dir(entity),
            "input_unadjusted_tb": self.get_unadjusted_tb_dir(entity),
            "input_manual_adjustments": self.get_manual_adjustments_dir(entity),
            "input_pre_adjusted_tb": self.get_pre_adjusted_tb_dir(entity),
            "input_notes_input": self.get_notes_input_dir(entity),
            "input_notes_trialbalance": self.get_notes_trialbalance_dir(entity),
            "output": self.get_output_dir(entity),
            "output_adjusted_tb": self.get_adjusted_tb_dir(entity),
            "output_generated_notes": self.get_generated_notes_dir(entity),
            "output_financial_statements": self.get_financial_statements_dir(entity),
        }

        # Create all directories
        for folder_type, path in folders.items():
            path.mkdir(parents=True, exist_ok=True)

        return folders

    def list_files_in_folder(self, folder_path: Path, pattern: str = "*") -> List[str]:
        """List all files in a folder matching pattern, excluding system files"""
        if not folder_path.exists():
            return []

        # System and hidden files to exclude
        excluded_files = {'.DS_Store', 'Thumbs.db', 'desktop.ini', '.gitkeep'}
        excluded_prefixes = ('.', '~', '__')

        files = []
        for f in folder_path.glob(pattern):
            if not f.is_file():
                continue

            # Skip if filename is in excluded list
            if f.name in excluded_files:
                continue

            # Skip if filename starts with excluded prefix
            if any(f.name.startswith(prefix) for prefix in excluded_prefixes):
                continue

            files.append(f.name)

        return sorted(files)  # Return sorted list for consistency

    def get_folder_info(self, entity: str = None) -> Dict[str, List[str]]:
        """
        Get information about all folders for an entity

        Returns:
            Dictionary with file listings for each folder
        """
        entity = (entity or self.entity).lower()

        return {
            "unadjusted_trialbalance": self.list_files_in_folder(self.get_unadjusted_tb_dir(entity)),
            "manual_adjustments": self.list_files_in_folder(self.get_manual_adjustments_dir(entity)),
            "pre_adjusted_trialbalance": self.list_files_in_folder(self.get_pre_adjusted_tb_dir(entity)),
            "adjusted_trialbalance": self.list_files_in_folder(self.get_adjusted_tb_dir(entity)),
            "generated_notes": self.list_files_in_folder(self.get_generated_notes_dir(entity)),
            "financial_statements": self.list_files_in_folder(self.get_financial_statements_dir(entity)),
        }

    def check_file_exists(self, file_path: Path) -> bool:
        """Check if a file exists"""
        return file_path.exists() and file_path.is_file()

    def get_available_entities(self) -> List[str]:
        """Get list of entities that have data folders, excluding system directories"""
        if not self.DATA_ROOT.exists():
            return []

        excluded_dirs = {'.git', '.DS_Store', '__pycache__', 'node_modules'}
        invalid_chars = {':', '*', '?', '"', '<', '>', '|', '\\'}  # Invalid entity name characters

        entities = []
        for d in self.DATA_ROOT.iterdir():
            if not d.is_dir():
                continue

            # Skip hidden directories (starting with .)
            if d.name.startswith('.'):
                continue

            # Skip excluded directories
            if d.name in excluded_dirs:
                continue

            # Skip directories with invalid characters (like backend.main:app)
            if any(char in d.name for char in invalid_chars):
                continue

            entities.append(d.name)

        return sorted(entities)  # Return sorted list for consistency


# Create a singleton instance for global use
_path_service_instance = None


def get_path_service(entity: str = None) -> PathService:
    """Get or create PathService instance"""
    global _path_service_instance

    if _path_service_instance is None:
        _path_service_instance = PathService(entity)
    elif entity is not None:
        _path_service_instance.set_entity(entity)

    return _path_service_instance