"""Company discovery and management service."""

import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from backend.config.settings import settings
from backend.models.company import (
    Company,
    CompanyWithCategories,
    NoteCategory,
    NoteInfo,
)

logger = logging.getLogger(__name__)


class CompanyService:
    """Service for managing company data and configuration."""

    @staticmethod
    def _parse_config_filename(filename: str) -> Optional[str]:
        """
        Private: Parse config filename to extract note number.

        Args:
            filename: Config filename to parse (e.g., "note24.json")

        Returns:
            Note number string or None
        """
        pattern = r"^note(\d+)\.json$"
        match = re.match(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _load_config_file(config_file: Path) -> Optional[Dict]:
        """
        Private: Load and parse a single config file.

        Args:
            config_file: Path to config file

        Returns:
            Config dictionary or None
        """
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config {config_file}: {e}")
            return None

    @staticmethod
    def _get_statement_type_from_path(category_folder: str) -> str:
        """
        Private: Convert category folder name to statement type.

        Args:
            category_folder: Folder name (e.g., "profit_and_loss", "balance_sheet", "cashflow_statement")

        Returns:
            Statement type string
        """
        # Map folder names to statement types
        folder_mapping = {
            "profit_and_loss": "profit-loss",
            "balance_sheet": "balance-sheet",
            "cash_flow": "cash-flow",
            "cashflow_statement": "cashflow",      # NEW
            "cash_flow_statement": "cashflow",     # NEW - alternative
            "important_notes": "important-notes",
        }
        
        normalized_folder = category_folder.lower().replace("-", "_")
        return folder_mapping.get(normalized_folder, "profit-loss")

    @staticmethod
    def _get_note_title(config_file: Path) -> str:
        """
        Private: Extract note title from config file.

        Args:
            config_file: Path to config file

        Returns:
            Note title or "Untitled Note" if not found
        """
        config = CompanyService._load_config_file(config_file)
        if config and "note_title" in config:
            return config["note_title"]
        return "Untitled Note"

    @staticmethod
    def discover_companies() -> Dict[str, Dict]:
        """
        Public: Scan config directory and discover all companies and their notes.

        Structure:
        config/
        ├── Entity_A/
        │   ├── profit_and_loss/
        │   ├── balance_sheet/
        │   ├── important_notes/
        │   └── cashflow_statement/  ← NEW
        
        Returns:
            Dictionary of company data
        """
        companies = defaultdict(
            lambda: {
                "notes": [],
                "csv_file": None,
                "notes_by_category": defaultdict(list),
            }
        )

        config_path = settings.CONFIG_DIR
        if not config_path.exists():
            return {}

        # Iterate through entity folders
        for entity_folder in config_path.iterdir():
            if not entity_folder.is_dir():
                continue

            entity_name = entity_folder.name

            # Iterate through category folders (profit_and_loss, balance_sheet, etc.)
            for category_folder in entity_folder.iterdir():
                if not category_folder.is_dir():
                    continue

                category_name = category_folder.name
                statement_type = CompanyService._get_statement_type_from_path(
                    category_name
                )

                # Handle statement-level configs (cashflow_statement folder)
                if category_name.lower() in ["cashflow_statement", "cash_flow_statement", "cashflow"]:
                    logger.info(f"   📊 Processing statement-level folder: {category_name}")
                    
                    # Look for the config file
                    possible_configs = [
                        "cashflow_statement_config.json",
                        "cash_flow_statement_config.json", 
                        "cashflow_config.json",
                        "config.json"
                    ]
                    
                    for config_name in possible_configs:
                        config_file = category_folder / config_name
                        
                        if config_file.exists():
                            logger.info(f"   ✅ Found statement config: {config_name}")
                            
                            # Load config to get title
                            config = CompanyService._load_config_file(config_file)
                            note_title = config.get("note_title", "Cash Flow Statement") if config else "Cash Flow Statement"
                            note_number = config.get("note_number", "CASHFLOW") if config else "CASHFLOW"
                            
                            # Create note info
                            note_info = {
                                "number": note_number,
                                "title": note_title
                            }
                            
                            companies[entity_name]["notes"].append(note_info)
                            companies[entity_name]["notes_by_category"][statement_type].append(note_info)
                            
                            # Get CSV file if specified
                            if config and "csv_file" in config and companies[entity_name]["csv_file"] is None:
                                companies[entity_name]["csv_file"] = config["csv_file"]
                            
                            break  # Found config, stop looking
                    
                    continue  # Skip the regular note*.json search for this folder

                # Standard handling for regular note configs (note24.json, note25.json, etc.)
                for config_file in category_folder.glob("note*.json"):
                    note_number = CompanyService._parse_config_filename(
                        config_file.name
                    )

                    if note_number:
                        # Get note title from config
                        note_title = CompanyService._get_note_title(config_file)

                        # Create NoteInfo object
                        note_info = {
                            "number": note_number,
                            "title": note_title
                        }

                        companies[entity_name]["notes"].append(note_info)
                        companies[entity_name]["notes_by_category"][
                            statement_type
                        ].append(note_info)

                        # Load config to get CSV file (only if not already set)
                        if companies[entity_name]["csv_file"] is None:
                            config = CompanyService._load_config_file(config_file)
                            if config and "csv_file" in config:
                                companies[entity_name]["csv_file"] = config["csv_file"]

            # After processing all configs, if csv_file still not set, try to find it
            if companies[entity_name]["csv_file"] is None:
                csv_from_folder = CompanyService._find_csv_in_entity_folder(entity_name)
                if csv_from_folder:
                    companies[entity_name]["csv_file"] = csv_from_folder

        # Sort notes numerically
        return CompanyService._sort_company_notes(companies)
    @staticmethod
    def _sort_company_notes(companies: Dict) -> Dict:
        """
        Private: Sort notes numerically for all companies.
        Handles both numeric note numbers (e.g., "24") and string note numbers (e.g., "CASHFLOW").

        Args:
            companies: Dictionary of company data

        Returns:
            Dictionary with sorted notes
        """
        def sort_key(note):
            """Sort numeric notes first, then alphabetic notes."""
            number = note["number"]
            try:
                # Try to convert to integer
                return (0, int(number))  # (0 = numeric, value)
            except ValueError:
                # String note number
                return (1, number)  # (1 = string, value)
        
        for company in companies.values():
            company["notes"] = sorted(company["notes"], key=sort_key)
            for category in company["notes_by_category"]:
                company["notes_by_category"][category] = sorted(
                    company["notes_by_category"][category], key=sort_key
                )

        return dict(companies)
    @staticmethod
    def _find_csv_in_entity_folder(company_name: str) -> Optional[str]:
        """
        Private: Find CSV file in entity's notes-input/Trialbalance folder.

        Looks for any .csv file in: data/{entity}/input/notes-input/Trialbalance/

        Args:
            company_name: Name of the company/entity

        Returns:
            Relative path to CSV file or None
        """
        from backend.services.path_service import PathService
        
        # Use PathService to get the correct directory
        path_service = PathService(company_name.lower())
        notes_tb_path = path_service.get_notes_trialbalance_dir(company_name.lower())

        logger.debug(f"Searching for CSV - Company: {company_name}, Path: {notes_tb_path}")

        if not notes_tb_path.exists():
            logger.warning(f"Notes trial balance folder not found for {company_name}: {notes_tb_path}")
            return None

        # Look for any CSV file in the Trialbalance folder
        csv_files = list(notes_tb_path.glob("*.csv"))
        logger.debug(f"Found {len(csv_files)} CSV file(s) in {notes_tb_path}")

        if csv_files:
            # Return full path to first CSV file found
            result = str(csv_files[0])
            logger.debug(f"Using CSV file: {result}")
            return result

        logger.warning(f"No CSV files found in {notes_tb_path}")
        return None

    @staticmethod
    def _find_csv_in_configs(company_name: str) -> Optional[str]:
        """
        Private: Search config files for CSV filename.

        Args:
            company_name: Name of the company

        Returns:
            CSV filename or None
        """
        entity_path = settings.CONFIG_DIR / company_name
        if not entity_path.exists():
            return None

        # Search in all category folders
        for category_folder in entity_path.iterdir():
            if not category_folder.is_dir():
                continue

            for config_file in category_folder.glob("note*.json"):
                config = CompanyService._load_config_file(config_file)
                if config and "csv_file" in config:
                    return config["csv_file"]

        return None

    @staticmethod
    def get_csv_file_for_company(company_name: str) -> str:
        """
        Public: Find CSV file for a company.

        Search order:
        1. Check config files for explicit csv_file
        2. Look in trialbalance/Entity_Name/ folder for any .csv
        3. Fallback to default Entity_Name/trial_balance.csv

        Args:
            company_name: Name of the company

        Returns:
            CSV filename path
        """
        # First check config files
        csv_from_config = CompanyService._find_csv_in_configs(company_name)
        if csv_from_config:
            return csv_from_config

        # Then check entity trial balance folder
        csv_from_folder = CompanyService._find_csv_in_entity_folder(company_name)
        if csv_from_folder:
            return csv_from_folder

        # Fallback to default
        return f"{company_name}/trial_balance.csv"

    @staticmethod
    def get_config_file_path(company_name: str, note_number: str) -> Optional[Path]:
        """
        Public: Get the full path to a config file for a specific note.
        
        Searches in category folders and also handles special statement configs.

        Args:
            company_name: Name of the company/entity
            note_number: Note number (e.g., "24", "CASHFLOW")

        Returns:
            Path to config file or None if not found
        """
        entity_path = settings.CONFIG_DIR / company_name
        
        logger.info(f"🔍 Searching for config file")
        logger.info(f"   Entity: {company_name}")
        logger.info(f"   Note Number: {note_number}")
        logger.info(f"   Entity Path: {entity_path}")
        
        if not entity_path.exists():
            logger.error(f"   ❌ Entity path does not exist: {entity_path}")
            return None

        # Special handling for statement-level configs (CASHFLOW, etc.)
        if note_number.upper() in ["CASHFLOW", "CASH-FLOW"]:
            logger.info(f"   🔄 Detected statement-level note: {note_number}")
            
            # Look for cashflow_statement folder
            statement_folders = ["cashflow_statement", "cash_flow_statement", "cashflow"]
            
            for folder_name in statement_folders:
                statement_folder = entity_path / folder_name
                logger.info(f"   Checking folder: {statement_folder}")
                
                if statement_folder.exists() and statement_folder.is_dir():
                    logger.info(f"   ✅ Found statement folder: {folder_name}")
                    
                    # Look for config files in this folder
                    possible_config_names = [
                        "cashflow_statement_config.json",
                        "cash_flow_statement_config.json",
                        "cashflow_config.json",
                        "config.json",
                    ]
                    
                    for config_name in possible_config_names:
                        config_path = statement_folder / config_name
                        logger.info(f"      Trying: {config_name}")
                        
                        if config_path.exists():
                            logger.info(f"   ✅ Found config file: {config_name}")
                            return config_path
        
        # Standard search in category folders (for regular notes like note24.json)
        logger.info(f"   🔄 Searching in category folders for note{note_number}.json")
        
        for category_folder in entity_path.iterdir():
            if not category_folder.is_dir():
                continue
            
            logger.info(f"   Checking category: {category_folder.name}")
            
            config_file = category_folder / f"note{note_number}.json"
            
            if config_file.exists():
                logger.info(f"   ✅ Found config: {category_folder.name}/note{note_number}.json")
                return config_file
        
        # List all available files for debugging
        logger.error(f"   ❌ Config file not found for note {note_number}")
        logger.error(f"   Available folders in {entity_path}:")
        try:
            for folder in entity_path.iterdir():
                if folder.is_dir():
                    logger.error(f"      📁 {folder.name}/")
                    json_files = list(folder.glob("*.json"))
                    for json_file in json_files:
                        logger.error(f"         - {json_file.name}")
        except Exception as e:
            logger.error(f"   Error listing folders: {e}")
        
        return None
    @staticmethod
    def get_all_companies() -> List[Company]:
        """Public: Get list of all companies."""
        companies_dict = CompanyService.discover_companies()

        companies_list = []
        for name, details in companies_dict.items():
            csv_file = details.get(
                "csv_file"
            ) or CompanyService.get_csv_file_for_company(name)

            # Convert note dicts to NoteInfo objects
            notes = [NoteInfo(**note) for note in details["notes"]]

            companies_list.append(
                Company(
                    name=name,
                    csv_file=csv_file,
                    notes_count=len(details["notes"]),
                    notes=notes,
                )
            )

        return sorted(companies_list, key=lambda x: x.name)

    @staticmethod
    def get_company_by_name(company_name: str) -> Optional[Company]:
        """Public: Get company details by name."""
        companies_dict = CompanyService.discover_companies()

        # Case-insensitive lookup
        company_name_lower = company_name.lower()
        matched_company = None
        for key in companies_dict:
            if key.lower() == company_name_lower:
                matched_company = key
                break

        if not matched_company:
            return None

        details = companies_dict[matched_company]
        csv_file = details.get("csv_file") or CompanyService.get_csv_file_for_company(
            matched_company
        )

        # Convert note dicts to NoteInfo objects
        notes = [NoteInfo(**note) for note in details["notes"]]

        return Company(
            name=matched_company,
            csv_file=csv_file,
            notes_count=len(details["notes"]),
            notes=notes,
        )

    @staticmethod
    def _build_category_metadata() -> Dict[str, Dict]:
        """
        Private: Get metadata for all category types.

        Returns:
            Dictionary of category metadata
        """
        return {
            "profit-loss": {
                "name": "Profit & Loss Statement",
                "description": "Revenue, expenses, and income statement notes",
            },
            "balance-sheet": {
                "name": "Balance Sheet",
                "description": "Assets, liabilities, and equity notes",
            },
            "cashflow": {  # ADD THIS
                "name": "Cash Flow Statement",
                "description": "Cash flows from operating, investing, and financing activities",
            },
            "cash-flow": {  # ADD THIS (alternative ID)
                "name": "Cash Flow Statement",
                "description": "Cash flows from operating, investing, and financing activities",
            },
            "important-notes": {
                "name": "Important Notes",
                "description": "Complex notes requiring multi-source integration and reconciliation",
            },
        }

    @staticmethod
    def _format_category(category_id: str, note_list: List[Dict]) -> NoteCategory:
        """
        Private: Format a single category with its metadata.

        Args:
            category_id: Category identifier
            note_list: List of note dictionaries in this category

        Returns:
            NoteCategory object
        """
        category_metadata = CompanyService._build_category_metadata()
        metadata = category_metadata.get(
            category_id,
            {
                "name": category_id.replace("-", " ").title(),
                "description": f"Notes for {category_id}",
            },
        )

        # Convert note dicts to NoteInfo objects
        notes = [NoteInfo(**note) for note in note_list]

        return NoteCategory(
            id=category_id,
            name=metadata["name"],
            description=metadata["description"],
            notes_count=len(note_list),
            notes=notes,
        )

    @staticmethod
    def get_company_with_categories(
        company_name: str,
    ) -> Optional[CompanyWithCategories]:
        """Public: Get company details with notes organized by categories."""
        companies_dict = CompanyService.discover_companies()

        # Case-insensitive lookup
        company_name_lower = company_name.lower()
        matched_company = None
        for key in companies_dict:
            if key.lower() == company_name_lower:
                matched_company = key
                break

        if not matched_company:
            return None

        details = companies_dict[matched_company]
        csv_file = details.get("csv_file") or CompanyService.get_csv_file_for_company(
            matched_company
        )

        # Build categories using private method
        categories = [
            CompanyService._format_category(category_id, note_list)
            for category_id, note_list in details["notes_by_category"].items()
        ]

        # Convert note dicts to NoteInfo objects
        notes = [NoteInfo(**note) for note in details["notes"]]

        return CompanyWithCategories(
            name=matched_company,
            csv_file=csv_file,
            notes_count=len(details["notes"]),
            notes=notes,
            categories=categories,
        )
