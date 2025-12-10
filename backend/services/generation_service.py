# ============================================================================
# FILE: backend/services/generation_service.py
# ============================================================================
"""Note generation service using Gemini AI - with Important Notes support and detailed logging."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

import pandas as pd

from backend.config.notes_prompts import (
    BALANCE_SHEET_TEMPLATE,
    CASH_FLOW_TEMPLATE,
    IMPORTANT_NOTES_TEMPLATE,
    PROFIT_LOSS_TEMPLATE,
)
from backend.config.settings import settings
from backend.models.generation import BatchGenerationStatus, GenerationResponse
from backend.services.company_service import CompanyService
from backend.services.currency_service import CurrencyService

# Configure logger
logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating financial notes using AI."""

    # Class variable for batch status storage
    batch_status: Dict[str, BatchGenerationStatus] = {}

    @staticmethod
    def _get_entity_currency(company_name: str) -> dict:
        """
        Get currency information for an entity from the currency mapping config.
        
        Args:
            company_name: Name of the company/entity
            
        Returns:
            Dictionary with currency information (symbol, code, format)
        """
        try:
            currency = CurrencyService.get_entity_currency(company_name)
            return currency.model_dump()
        except Exception as e:
            logger.error(f"❌ Error loading currency info: {e}")
            # Default to INR on error
            return {
                "entity_name": company_name,
                "default_currency": "INR",
                "currency_symbol": "₹",
                "currency_name": "Indian Rupee",
                "decimal_places": 2,
                "format": "₹#,##,##0.00"
            }

    @staticmethod
    def _build_cashflow_categories(config: dict) -> dict:
        """Build categories text for cash flow statement sections."""
        logger.info("🔄 Building Cash Flow categories from config sections")
        
        categories_text = {}
        sections = config.get("sections", {})
        
        # Operating Activities - Adjustments
        if "operating_activities" in sections:
            operating_adjustments = []
            adjustments_section = sections["operating_activities"].get("adjustments_section", {})
            for cat in adjustments_section.get("categories", []):
                ind_as_minor_str = ', '.join(cat['ind_as_minor'])
                # Format for markdown table
                operating_adjustments.append(f"| {cat['line_item']} | [Amount] |")
            categories_text['operating_adjustments'] = '\n'.join(operating_adjustments) if operating_adjustments else "| [No adjustments] | |"
            
            # Working Capital Changes
            working_capital_items = []
            wc_changes = sections["operating_activities"].get("working_capital_changes", {})
            for cat in wc_changes.get("categories", []):
                working_capital_items.append(f"| {cat['line_item']} | [Amount] |")
            categories_text['working_capital_changes'] = '\n'.join(working_capital_items) if working_capital_items else "| [No changes] | |"
        
        # Investing Activities
        if "investing_activities" in sections:
            investing_items = []
            for cat in sections["investing_activities"].get("categories", []):
                investing_items.append(f"| {cat['line_item']} | [Amount] |")
            categories_text['investing_items'] = '\n'.join(investing_items) if investing_items else "| [No items] | |"
        
        # Financing Activities
        if "financing_activities" in sections:
            financing_items = []
            for cat in sections["financing_activities"].get("categories", []):
                financing_items.append(f"| {cat['line_item']} | [Amount] |")
            categories_text['financing_items'] = '\n'.join(financing_items) if financing_items else "| [No items] | |"
        
        logger.info(f"✅ Built {len(categories_text)} category sections")
        return categories_text



    @staticmethod
    def _get_template_for_statement_type(statement_type: str) -> str:
        """
        Private: Get the appropriate template based on statement type.

        Args:
            statement_type: Type of financial statement

        Returns:
            Template string
        """
        logger.info(f"📄 Getting template for statement type: {statement_type}")
        
        # Normalize statement type
        statement_type_lower = statement_type.lower()
        
        templates = {
            "profit-loss": PROFIT_LOSS_TEMPLATE,
            "balance-sheet": BALANCE_SHEET_TEMPLATE,
            "cash-flow": CASH_FLOW_TEMPLATE,
            "cashflow": CASH_FLOW_TEMPLATE,  # Alternative spelling
            "important-notes": IMPORTANT_NOTES_TEMPLATE,
        }
        
        template = templates.get(statement_type_lower, PROFIT_LOSS_TEMPLATE)
        logger.info(f"✅ Template selected: {statement_type} (length: {len(template)} chars)")


        return template
    @staticmethod
    def _load_config(config_file_path: Path) -> Optional[dict]:
        """
        Private: Load JSON configuration file from full path.

        Args:
            config_file_path: Full path to config file

        Returns:
            Config dictionary or None
        """
        logger.info(f"📥 Loading configuration from: {config_file_path}")
        try:
            with open(config_file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"✅ Configuration loaded successfully")
            logger.debug(f"📋 Config content:\n{json.dumps(config, indent=2)}")
            return config
        except Exception as e:
            logger.error(f"❌ Error loading config {config_file_path}: {e}")
            return None

    @staticmethod
    def _build_categories_list(categories: list) -> str:
        """
        Private: Format categories list for prompt.

        Args:
            categories: List of category names

        Returns:
            Formatted string
        """
        logger.info(f"📝 Building categories list with {len(categories)} categories")
        categories_list = "\n".join([f'- "{cat}"' for cat in categories])
        logger.debug(f"Categories:\n{categories_list}")
        return categories_list

    @staticmethod
    def _build_output_rows(output_format: list, currency_symbol: str = '₹') -> str:
        """
        Private: Format output rows for prompt.

        Args:
            output_format: List of output format specifications
            currency_symbol: Currency symbol to use (default: ₹)

        Returns:
            Formatted string
        """
        logger.info(f"📝 Building output rows with {len(output_format)} items using {currency_symbol}")
        output_rows = []
        for row in output_format:
            if row.get("is_header", False):
                output_rows.append(f"| {row['label']} | |")
            else:
                output_rows.append(f"| {row['label']} | {currency_symbol} [Sum] |")

        result = "\n".join(output_rows)
        logger.debug(f"Output rows:\n{result}")
        return result

    @staticmethod
    def _build_auxiliary_sources(auxiliary_files: list) -> str:
        """
        Private: Format auxiliary data sources for prompt.

        Args:
            auxiliary_files: List of auxiliary file configurations

        Returns:
            Formatted string
        """
        if not auxiliary_files:
            logger.info("📂 No auxiliary files specified")
            return "None"

        logger.info(f"📂 Building auxiliary sources list with {len(auxiliary_files)} files")
        sources = []
        for aux_file in auxiliary_files:
            # Handle both 'label' (important notes) and 'file_name' (cash flow) as label
            label = aux_file.get('label') or aux_file.get('file_name', 'Unknown File')
            
            # Handle both 'description' (important notes) and 'purpose' (cash flow) as description
            description = aux_file.get('description') or aux_file.get('purpose', 'N/A')
            
            # Get file path
            file_path = aux_file.get('file_path', 'N/A')
            
            sources.append(
                f"- **{label}**: {file_path} - {description}"
            )
        result = "\n".join(sources)
        logger.debug(f"Auxiliary sources:\n{result}")
        return result
    @staticmethod
    def _build_gl_breakdown_format(gl_breakdown_config: list) -> str:
        """
        Private: Format GL breakdown structure for prompt.

        Args:
            gl_breakdown_config: GL breakdown configuration

        Returns:
            Formatted string
        """
        logger.info(f"📊 Building GL breakdown format with {len(gl_breakdown_config)} sections")
        output = []
        for section in gl_breakdown_config:
            output.append(f"\n**{section['section']}:**")
            output.append(f"Format: {section['format']}")
            if section.get('show_subtotal'):
                output.append(f"**{section['subtotal_label']}:** | **₹[Total]**")
            output.append("")
        result = "\n".join(output)
        logger.debug(f"GL breakdown format:\n{result}")
        return result

    @staticmethod
    def _build_summary_table_format(summary_config: list) -> str:
        """
        Private: Format summary table structure for prompt.

        Args:
            summary_config: Summary table configuration

        Returns:
            Formatted string
        """
        logger.info(f"📊 Building summary table format with {len(summary_config)} items")
        output = ["| Particulars | Amount (₹) |", "|---|---|"]
        for item in summary_config:
            if item.get("is_total"):
                output.append(f"| **{item['label']}** | **₹[Total]** |")
            else:
                output.append(f"| {item['label']} | ₹[Amount] |")
        result = "\n".join(output)
        logger.debug(f"Summary table format:\n{result}")
        return result

    @staticmethod
    def _build_reconciliation_format(reconciliation_config: list) -> str:
        """
        Private: Format reconciliation structure for prompt.

        Args:
            reconciliation_config: Reconciliation configuration

        Returns:
            Formatted string
        """
        logger.info(f"📊 Building reconciliation format with {len(reconciliation_config)} items")
        output = ["| Particulars | Amount (₹) |", "|---|---|"]
        for item in reconciliation_config:
            if item.get("is_total") or item.get("is_bold"):
                output.append(f"| **{item['label']}** | **₹[Amount]** |")
            else:
                output.append(f"| {item['label']} | ₹[Amount] |")
        result = "\n".join(output)
        logger.debug(f"Reconciliation format:\n{result}")
        return result

    @staticmethod
    def _build_prompt(config: dict, company_name: str = None) -> str:
        """
        Private: Build dynamic prompt from JSON configuration.

        Args:
            config: Configuration dictionary
            company_name: Company name for currency lookup

        Returns:
            Complete prompt string
        """
        logger.info("=" * 80)
        logger.info("🔧 BUILDING SYSTEM PROMPT")
        logger.info("=" * 80)
        
        # Get currency information for the entity
        currency_info = GenerationService._get_entity_currency(company_name) if company_name else None
        currency_symbol = currency_info['currency_symbol'] if currency_info else '₹'
        currency_name = currency_info['currency_name'] if currency_info else 'Indian Rupee'
        
        logger.info(f"💱 Using currency: {currency_symbol} ({currency_name})")
        
        statement_type = config.get("statement_type", "profit-loss")
        note_number = config.get("note_number", "")
        note_title = config.get("note_title", "")
        
        logger.info(f"📋 Note Number: {note_number}")
        logger.info(f"📋 Note Title: {note_title}")
        logger.info(f"📋 Statement Type: {statement_type}")
        
        logger.info(f"📋 Note Number: {note_number}")
        logger.info(f"📋 Note Title: {note_title}")
        logger.info(f"📋 Statement Type: {statement_type}")
        
        template = GenerationService._get_template_for_statement_type(statement_type)

        # Build categories list for standard statements
        if statement_type not in ["important-notes", "cash-flow", "cashflow"]:
            categories_list = GenerationService._build_categories_list(config.get("categories", []))

        # For CASH FLOW statements
        if statement_type in ["cash-flow", "cashflow"]:
            logger.info("📝 Building CASH FLOW STATEMENT prompt")
            
            cashflow_categories = GenerationService._build_cashflow_categories(config)
            auxiliary_sources = GenerationService._build_auxiliary_sources(
                config.get("auxiliary_files", [])
            )
            
            period_column = config.get("period_column", "Total Jun'25")
            prior_period_column = config.get("prior_period_column", "N/A")
            
            prompt = template.format(
                note_title=config["note_title"],
                note_number=config["note_number"],
                note_title_upper=config["note_title"].upper(),
                period_column=period_column,
                prior_period_column=prior_period_column,
                summation_rule=config.get("summation_rule", "Algebraic sum"),
                operating_adjustments=cashflow_categories.get('operating_adjustments', ''),
                working_capital_changes=cashflow_categories.get('working_capital_changes', ''),
                investing_items=cashflow_categories.get('investing_items', ''),
                financing_items=cashflow_categories.get('financing_items', ''),
                auxiliary_sources=auxiliary_sources,
                output_structure='',
                additional_instructions=config.get("additional_instructions", ""),
            )

        # For important-notes
        elif statement_type == "important-notes":
            logger.info("📝 Building IMPORTANT NOTES prompt")
            
            categories_list = GenerationService._build_categories_list(config.get("categories", []))
            auxiliary_sources = GenerationService._build_auxiliary_sources(
                config.get("auxiliary_files", [])
            )

            output_format_config = config.get("output_format", {})
            gl_breakdown_format = GenerationService._build_gl_breakdown_format(
                output_format_config.get("gl_breakdown", [])
            )
            summary_table_format = GenerationService._build_summary_table_format(
                output_format_config.get("summary_table", [])
            )
            reconciliation_format = GenerationService._build_reconciliation_format(
                output_format_config.get("reconciliation", [])
            )

            prompt = template.format(
                note_title=config["note_title"],
                note_number=config["note_number"],
                note_title_upper=config["note_title"].upper(),
                multi_source_rule=config.get(
                    "multi_source_rule",
                    "Integrate data from multiple sources as specified."
                ),
                summation_rule=config.get(
                    "summation_rule",
                    "Use appropriate accounting treatment based on statement type.",
                ),
                period_handling=config.get(
                    "period_handling",
                    "Process data for the specified period."
                ),
                categories_list=categories_list,
                auxiliary_sources=auxiliary_sources,
                gl_breakdown_format=gl_breakdown_format,
                summary_table_format=summary_table_format,
                reconciliation_format=reconciliation_format,
                additional_instructions=config.get("additional_instructions", ""),
            )
        
        # For standard statements (profit-loss, balance-sheet)
        else:
            logger.info("📝 Building STANDARD financial statement prompt")
            
            output_rows_str = GenerationService._build_output_rows(
                config.get("output_format", []),
                currency_symbol
            )

            period_column = config.get("period_column", "Total Jun'25")
            logger.info(f"📅 Period Column for Prompt: '{period_column}'")

            prompt = template.format(
                note_title=config["note_title"],
                note_number=config["note_number"],
                note_title_upper=config["note_title"].upper(),
                period_column=period_column,
                currency_symbol=currency_symbol,
                currency_name=currency_name,
                summation_rule=config.get(
                    "summation_rule",
                    "Use appropriate accounting treatment based on statement type.",
                ),
                categories_list=categories_list,
                output_rows=output_rows_str,
                additional_instructions=config.get("additional_instructions", ""),
            )

        logger.info(f"\n✅ SYSTEM PROMPT BUILT (Length: {len(prompt)} characters)")
        logger.info("=" * 80)
        
        return prompt
    @staticmethod
    def _read_csv(file_path: str, period_column: str = None) -> Optional[str]:
        """
        Private: Read CSV or Excel file and return its content as a string.

        Args:
            file_path: Path to CSV/Excel file (absolute path)
            period_column: Optional period column name to highlight in logs

        Returns:
            CSV content as string or None
        """
        logger.info(f"📖 Reading file: {file_path}")
        if period_column:
            logger.info(f"🎯 Target Period Column: '{period_column}'")
        
        try:
            file_full_path = Path(file_path)

            # Check if file exists
            if not file_full_path.exists():
                logger.error(f"❌ File not found at {file_full_path}")
                return None

            logger.info(f"✅ File exists, reading from: {file_full_path}")
            
            # Determine file type and read accordingly
            file_extension = file_full_path.suffix.lower()
            
            if file_extension in ['.xlsx', '.xls']:
                logger.info(f"📊 Detected Excel file, using pd.read_excel()")
                df = pd.read_excel(file_full_path)
            elif file_extension == '.csv':
                logger.info(f"📄 Detected CSV file, using pd.read_csv()")
                df = pd.read_csv(file_full_path)
            else:
                logger.warning(f"⚠️  Unknown file extension: {file_extension}, trying CSV")
                df = pd.read_csv(file_full_path)
            
            csv_content = df.to_csv(index=False)
            
            logger.info(f"✅ File read successfully")
            logger.info(f"📊 Stats: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"📊 All Columns Available: {list(df.columns)}")
            
            # Check if period column exists and show sample data
            if period_column:
                if period_column in df.columns:
                    logger.info(f"✅ Period column '{period_column}' FOUND in file")
                    non_zero = df[df[period_column] != 0][period_column]
                    if len(non_zero) > 0:
                        logger.info(f"📊 Sample values from '{period_column}':")
                        logger.info(f"   - Total non-zero entries: {len(non_zero)}")
                        logger.info(f"   - Sample values: {non_zero.head(5).tolist()}")
                        logger.info(f"   - Sum of column: {df[period_column].sum()}")
                    else:
                        logger.warning(f"⚠️  Column '{period_column}' exists but all values are zero")
                else:
                    logger.error(f"❌ Period column '{period_column}' NOT FOUND in file!")
                    logger.error(f"   Available columns: {list(df.columns)}")
            
            logger.info(f"📊 Total characters: {len(csv_content)}")
            
            return csv_content
            
        except Exception as e:
            logger.error(f"❌ Error reading file {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    @staticmethod
    def _load_auxiliary_files(auxiliary_files: list) -> Dict[str, str]:
        """
        Private: Load auxiliary data files for important notes and cash flow.

        Args:
            auxiliary_files: List of auxiliary file configurations (with full_path)

        Returns:
            Dictionary of label -> CSV content
        """
        logger.info("=" * 80)
        logger.info("📂 LOADING AUXILIARY FILES")
        logger.info("=" * 80)
        logger.info(f"Total auxiliary files to load: {len(auxiliary_files)}")
        
        auxiliary_data = {}

        for idx, aux_file in enumerate(auxiliary_files, 1):
            label = aux_file.get("label", aux_file.get("file_name", f"File_{idx}"))
            file_path = aux_file.get("full_path") or str(Path(aux_file["file_path"]) / aux_file["file_name"])
            description = aux_file.get("description", aux_file.get("purpose", "N/A"))
            required = aux_file.get("required", False)
            
            logger.info(f"\n📂 Auxiliary File #{idx}:")
            logger.info(f"  - Label: {label}")
            logger.info(f"  - File Path: {file_path}")
            logger.info(f"  - Description: {description}")
            logger.info(f"  - Required: {required}")

            content = GenerationService._read_csv(file_path)
            if content:
                auxiliary_data[label] = content
                logger.info(f"  ✅ Loaded successfully ({len(content)} characters)")
            else:
                if required:
                    logger.error(f"  ❌ Required file not found: {file_path}")
                else:
                    logger.warning(f"  ⚠️  Optional file not found: {file_path}")

        logger.info(f"\n✅ Successfully loaded {len(auxiliary_data)}/{len(auxiliary_files)} auxiliary files")
        logger.info("=" * 80)
        
        return auxiliary_data

    @staticmethod
    def _build_user_prompt(config: dict, csv_data: str, auxiliary_data: Dict[str, str] = None) -> str:
        """
        Private: Build user prompt with trial balance data.
        
        Args:
            config: Configuration dictionary
            csv_data: CSV content as string
            auxiliary_data: Optional dictionary of auxiliary file contents

        Returns:
            User prompt string
        """
        logger.info("=" * 80)
        logger.info("👤 BUILDING USER PROMPT")
        logger.info("=" * 80)

        statement_type = config.get("statement_type", "profit-loss")
        logger.info(f"📊 Statement Type: {statement_type}")
        logger.info(f"📄 CSV Data Length: {len(csv_data)} characters")

        # Check if multi-source (important notes or cash flow)
        if config.get("multi_source_integration") or statement_type in ["cash-flow", "cashflow"]:
            logger.info(f"🔀 Building MULTI-SOURCE user prompt")
            
            prompt = """
    Please generate the financial note as per the instructions.

    **TRIAL BALANCE DATA:**
    {csv_data}

    """
            logger.info(f"📄 Trial Balance included in prompt")
            
            if auxiliary_data:
                logger.info(f"\n📂 Including {len(auxiliary_data)} auxiliary files in prompt:")
                prompt += "**AUXILIARY DATA FILES:**\n\n"
                for label, content in auxiliary_data.items():
                    logger.info(f"  - {label}: {len(content)} characters")
                    prompt += f"### {label} ###\n{content}\n\n"

            # Add period-specific instructions for cash flow
            if statement_type in ["cash-flow", "cashflow"]:
                period_column = config.get("period_column", "Total Jun'25")
                prior_period_column = config.get("prior_period_column", "N/A")
                
                logger.info(f"\n📅 Adding period instructions for cash flow:")
                logger.info(f"  - Current Period: {period_column}")
                logger.info(f"  - Prior Period: {prior_period_column}")
                
                prompt += f"""
    **PERIOD COLUMNS:**
    - Current Period: Use column '{period_column}' for current year values
    - Prior Period: Use column '{prior_period_column}' for working capital calculations

    """

            # Add period-specific instructions for important notes with multiple periods
            elif "periods" in config:
                periods = config["periods"]
                logger.info(f"\n📅 Including {len(periods)} periods in prompt:")
                prompt += "**PERIODS TO ANALYZE:**\n"
                for period in periods:
                    period_name = period['period_name']
                    period_column = period['period_column']
                    logger.info(f"  - {period_name}: Column '{period_column}'")
                    prompt += f"- {period_name}: Use column '{period_column}'\n"
                prompt += "\n"

            prompt = prompt.format(csv_data=csv_data)

        elif "opening_balance_column" in config and "closing_balance_column" in config:
            # Inventory handling
            opening_col = config['opening_balance_column']
            closing_col = config['closing_balance_column']
            
            logger.info(f"📊 Building INVENTORY BALANCE user prompt")
            logger.info(f"  - Opening Balance Column: {opening_col}")
            logger.info(f"  - Closing Balance Column: {closing_col}")
            
            prompt = f"""
    Here is the trial balance data. Please generate the financial note as per the instructions.
    Use the '{opening_col}' column for opening inventory values.
    Use the '{closing_col}' column for closing inventory values.

    {csv_data}
    """
        else:
            # Standard prompt with period column
            period_column = config.get("period_column", "Total Jun'25")
            logger.info(f"📊 Building STANDARD user prompt")
            logger.info(f"  - Period Column: {period_column}")
            
            prompt = f"""
    Here is the trial balance data. Please generate the financial note as per the instructions.
    Focus on the values in the '{period_column}' column for your calculations.

    {csv_data}
    """

        logger.info(f"\n✅ USER PROMPT BUILT (Length: {len(prompt)} characters)")
        logger.info("=" * 80)
        
        return prompt

    @staticmethod
    def _generate_note_with_ai(
        csv_data: str, system_prompt: str, config: dict, auxiliary_data: Dict[str, str] = None
    ) -> Optional[str]:
        """
        Private: Generate financial notes using configured LLM provider.

        Args:
            csv_data: CSV content
            system_prompt: System instructions
            config: Configuration dictionary
            auxiliary_data: Optional auxiliary file contents

        Returns:
            Generated note content or None
        """
        logger.info("=" * 80)
        logger.info("🤖 CALLING AI SERVICE")
        logger.info("=" * 80)
        logger.info(f"System Prompt Length: {len(system_prompt)} characters")
        logger.info(f"User Prompt will be built inside LLM service")
        
        try:
            from backend.services.llm_service import LLMService

            # Build user prompt with correct parameter order
            user_prompt = GenerationService._build_user_prompt(config, csv_data, auxiliary_data)
            
            logger.info(f"User Prompt Length: {len(user_prompt)} characters")
            logger.info(f"🚀 Sending request to LLM service...")

            # Generate using configured LLM provider
            result = LLMService.generate_content(system_prompt, user_prompt)

            if result:
                logger.info(f"✅ AI generation successful")
                logger.info(f"📄 Generated content length: {len(result)} characters")
            else:
                logger.error(f"❌ AI generation returned None")
            
            logger.info("=" * 80)
            return result

        except Exception as e:
            logger.error(f"❌ Error generating note with AI: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.info("=" * 80)
            return None

    @staticmethod
    def _save_generated_note(
            content: str,
            company_name: str,
            note_number: str,
            note_title: str = None) -> Path:
        """
        Private: Save generated note to file in entity-specific generated_notes folder.

        Args:
            content: Generated note content
            company_name: Company name
            note_number: Note number
            note_title: Optional note title for logical naming

        Returns:
            Path to saved file
        """
        logger.info("=" * 80)
        logger.info("💾 SAVING GENERATED NOTE")
        logger.info("=" * 80)
        logger.info(f"Company: {company_name}")
        logger.info(f"Note Number: {note_number}")
        logger.info(f"Note Title: {note_title}")
        
        from backend.services.path_service import PathService

        # Use PathService to get the correct directory
        path_service = PathService(company_name)
        notes_dir = path_service.get_generated_notes_dir(company_name)
        notes_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Output directory: {notes_dir}")

        # Create logical filename - overwrite if exists
        if note_title:
            # Clean title for filename
            clean_title = note_title.replace(" ", "_").replace("/", "_").replace("&", "and")
            output_filename = f"Note_{note_number}_{clean_title}.md"
        else:
            output_filename = f"Note_{note_number}.md"

        output_file = notes_dir / output_filename
        
        logger.info(f"📄 Output filename: {output_filename}")
        logger.info(f"📄 Full path: {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ Note saved successfully")
        logger.info(f"📊 File size: {output_file.stat().st_size} bytes")
        logger.info("=" * 80)
        
        return output_file

    @staticmethod
    def _resolve_period_column(config: dict, company_name: str) -> str:
        """
        Resolve the period column to use, prioritizing runtime config over JSON.
        
        Priority:
        1. Runtime period set via PeriodConfig (highest priority)
        2. Period column in JSON config
        3. Auto-detect from entity's trial balance file
        4. Default fallback
        
        Args:
            config: JSON configuration
            company_name: Name of the company
            
        Returns:
            Period column name to use
        """
        logger.info("=" * 80)
        logger.info("📅 RESOLVING PERIOD COLUMN")
        logger.info("=" * 80)
        
        # Import here to avoid circular imports
        from backend.config.period_config import period_config
        from backend.services.period_discovery_service import PeriodDiscoveryService
        
        # Check if runtime period is set
        runtime_period_column = period_config.get_current_period_column(default=None)
        config_period_column = config.get("period_column")
        
        if runtime_period_column:
            logger.info(f"🎯 Using RUNTIME period: {period_config.get_current_period()}")
            logger.info(f"   Column: {runtime_period_column}")
            
            if config_period_column and config_period_column != runtime_period_column:
                logger.warning(f"⚠️  Overriding JSON period_column '{config_period_column}' with runtime period")
            
            logger.info("=" * 80)
            return runtime_period_column
        
        elif config_period_column:
            logger.info(f"📄 Using JSON config period_column: {config_period_column}")
            logger.info("=" * 80)
            return config_period_column
        
        else:
            # Try to auto-detect period from entity's trial balance
            # Ensure entity name is lowercase for path matching
            entity_lower = company_name.lower()
            logger.info(f"🔍 Auto-detecting period for entity: {entity_lower}")
            try:
                discovered_periods = PeriodDiscoveryService.discover_periods_for_entity(entity_lower)
                logger.info(f"   Discovered periods: {discovered_periods}")
                
                if discovered_periods:
                    # Sort periods and get the most recent one
                    sorted_periods = PeriodDiscoveryService.sort_periods(discovered_periods)
                    latest_period_key = list(sorted_periods.keys())[0]
                    latest_period_column = sorted_periods[latest_period_key]
                    logger.info(f"✅ Auto-detected period: {latest_period_key} -> {latest_period_column}")
                    logger.info("=" * 80)
                    return latest_period_column
                else:
                    logger.warning(f"⚠️  No periods discovered for entity {entity_lower}")
                    logger.warning(f"   Check if trial balance file exists in data/{entity_lower}/input/unadjusted-trialbalance/")
            except Exception as e:
                logger.warning(f"⚠️  Error auto-detecting period: {e}")
                import traceback
                logger.warning(traceback.format_exc())
            
            # Final fallback
            default = "Total Mar'25"
            logger.warning(f"⚠️  No period specified, using default: {default}")
            logger.info("=" * 80)
            return default

    @staticmethod
    def generate_single_note(company_name: str, note_number: str) -> GenerationResponse:
        """
        Public: Generate a single note for a company.

        Args:
            company_name: Name of the company/entity
            note_number: Note number to generate

        Returns:
            GenerationResponse object
        """
        # ============================================================================
        # SETUP INDIVIDUAL LOG FILE FOR THIS NOTE
        # ============================================================================
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Get timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create temporary log filename
        temp_log_filename = f"{timestamp}_Note{note_number}_{company_name}.log"
        log_path = logs_dir / temp_log_filename
        
        # Get the generation service logger
        gen_logger = logging.getLogger('backend.services.generation_service')
        gen_logger.handlers.clear()  # Remove all handlers
        gen_logger.propagate = False  # Don't send to parent loggers
        gen_logger.setLevel(logging.INFO)
        
        # Create ONLY file handler with simple message-only format
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')  # Simple format - just the message
        file_handler.setFormatter(formatter)
        
        # Add file handler to generation service logger
        gen_logger.addHandler(file_handler)
        
        # Log start
        gen_logger.info("\n" + "=" * 80)
        gen_logger.info("🚀 STARTING NOTE GENERATION")
        gen_logger.info("=" * 80)
        gen_logger.info(f"🏢 Company/Entity: {company_name}")
        gen_logger.info(f"📝 Note Number: {note_number}")
        gen_logger.info(f"⏰ Timestamp: {datetime.now().isoformat()}")
        gen_logger.info(f"📄 Log File: {log_path}")
        gen_logger.info("=" * 80)
        
        try:
            # Get config file path
            gen_logger.info("\n🔍 Locating configuration file...")
            config_file_path = CompanyService.get_config_file_path(
                company_name, note_number
            )

            if config_file_path is None:
                gen_logger.error(f"❌ Configuration file not found")
                file_handler.close()
                gen_logger.removeHandler(file_handler)
                return GenerationResponse(
                    success=False,
                    message=f"Configuration file not found for {company_name}, note {note_number}",
                    note_number=note_number,
                )
            
            gen_logger.info(f"✅ Config file found: {config_file_path}")

            # Load config
            config = GenerationService._load_config(config_file_path)
            if config is None:
                gen_logger.error(f"❌ Failed to load configuration")
                file_handler.close()
                gen_logger.removeHandler(file_handler)
                return GenerationResponse(
                    success=False,
                    message=f"Failed to load configuration file: {config_file_path}",
                    note_number=note_number,
                )

            # Get statement type early
            statement_type = config.get("statement_type", "profit-loss")
            gen_logger.info(f"\n📊 Statement Type: {statement_type}")

            # Rename log file with note title
            note_title = config.get("note_title", "Untitled")
            clean_note_title = note_title.replace(" ", "_").replace("/", "_").replace("&", "and")
            final_log_filename = f"{timestamp}_Note{note_number}_{clean_note_title}_{company_name}.log"
            final_log_path = logs_dir / final_log_filename
            
            # Close handler, rename file, reopen
            file_handler.close()
            gen_logger.removeHandler(file_handler)
            log_path.rename(final_log_path)
            
            # Create new handler with final filename
            file_handler = logging.FileHandler(final_log_path, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            gen_logger.addHandler(file_handler)
            
            gen_logger.info(f"📄 Log file renamed to: {final_log_filename}")

            # Resolve period dynamically
            resolved_period = GenerationService._resolve_period_column(config, company_name)
            config["period_column"] = resolved_period
            
            gen_logger.info(f"\n📅 Final Resolved Period Column: {resolved_period}")
            
            # For cash flow, also log prior period if available
            if statement_type in ["cash-flow", "cashflow"]:
                prior_period = config.get("prior_period_column", "N/A")
                gen_logger.info(f"📅 Prior Period Column: {prior_period}")

            # Get CSV file
            gen_logger.info("\n🔍 Locating CSV file...")
            csv_file = config.get("csv_file") or CompanyService.get_csv_file_for_company(company_name)
            
            if not csv_file:
                gen_logger.error(f"❌ CSV file not found")
                file_handler.close()
                gen_logger.removeHandler(file_handler)
                return GenerationResponse(
                    success=False,
                    message=f"CSV file not found for {company_name}",
                    note_number=note_number,
                )
            
            gen_logger.info(f"✅ CSV file located: {csv_file}")

            # Build prompt
            gen_logger.info("\n🔧 Building system prompt...")
            system_prompt = GenerationService._build_prompt(config, company_name)

            # Read CSV with period column info
            gen_logger.info("\n📖 Reading CSV data...")
            csv_data = GenerationService._read_csv(csv_file, resolved_period)
            if csv_data is None:
                gen_logger.error(f"❌ Failed to read CSV file")
                file_handler.close()
                gen_logger.removeHandler(file_handler)
                return GenerationResponse(
                    success=False,
                    message=f"Failed to read CSV file: {csv_file}",
                    note_number=note_number,
                )

            # Load auxiliary files if needed (for important-notes, cash-flow, or cashflow)
            auxiliary_data = None
            if statement_type in ["important-notes", "cash-flow", "cashflow"] and config.get("auxiliary_files"):
                gen_logger.info(f"\n📂 Note type '{statement_type}' requires auxiliary files")
                
                # Process auxiliary file paths - replace {entity} placeholder
                auxiliary_files = config.get("auxiliary_files", [])
                processed_aux_files = []
                
                for aux_file in auxiliary_files:
                    # Create a copy to avoid modifying original config
                    aux_file_copy = aux_file.copy()
                    
                    # Replace {entity} placeholder in file_path
                    if "{entity}" in aux_file_copy.get("file_path", ""):
                        aux_file_copy["file_path"] = aux_file_copy["file_path"].replace("{entity}", company_name)
                        gen_logger.info(f"  🔄 Resolved path: {aux_file_copy['file_path']}")
                    
                    # Build full file path
                    file_path = Path(aux_file_copy["file_path"]) / aux_file_copy["file_name"]
                    aux_file_copy["full_path"] = str(file_path)
                    
                    processed_aux_files.append(aux_file_copy)
                
                # Update config with processed paths
                config["auxiliary_files"] = processed_aux_files
                
                # Load the auxiliary files
                auxiliary_data = GenerationService._load_auxiliary_files(processed_aux_files)
                
                if auxiliary_data:
                    gen_logger.info(f"✅ Loaded {len(auxiliary_data)} auxiliary file(s)")
                else:
                    gen_logger.warning(f"⚠️  No auxiliary files loaded")
                    
                    # Check if any required files are missing
                    required_files = [f for f in processed_aux_files if f.get("required", False)]
                    if required_files:
                        missing = [f["file_name"] for f in required_files]
                        gen_logger.error(f"❌ Required auxiliary files missing: {missing}")
                        file_handler.close()
                        gen_logger.removeHandler(file_handler)
                        return GenerationResponse(
                            success=False,
                            message=f"Required auxiliary files not found: {', '.join(missing)}",
                            note_number=note_number,
                        )
            else:
                gen_logger.info("\n📂 No auxiliary files required for this note type")

            # Generate with AI
            gen_logger.info("\n🤖 Calling AI service for content generation...")
            result = GenerationService._generate_note_with_ai(
                csv_data, system_prompt, config, auxiliary_data
            )
            
            if result is None:
                gen_logger.error(f"❌ AI generation failed")
                file_handler.close()
                gen_logger.removeHandler(file_handler)
                return GenerationResponse(
                    success=False,
                    message="Failed to generate note using AI",
                    note_number=note_number,
                )

            # Save output
            gen_logger.info("\n💾 Saving generated note...")
            output_file = GenerationService._save_generated_note(
                result, company_name, note_number, note_title
            )

            gen_logger.info("\n" + "=" * 80)
            gen_logger.info("✅ NOTE GENERATION COMPLETED SUCCESSFULLY")
            gen_logger.info("=" * 80)
            gen_logger.info(f"📋 Note Type: {statement_type}")
            gen_logger.info(f"📋 Note Number: {note_number}")
            gen_logger.info(f"📋 Note Title: {note_title}")
            gen_logger.info(f"📄 Output file: {output_file}")
            gen_logger.info(f"📊 Content length: {len(result)} characters")
            gen_logger.info(f"📝 Log saved to: {final_log_path}")
            
            if auxiliary_data:
                gen_logger.info(f"📂 Auxiliary files used: {len(auxiliary_data)}")
            
            gen_logger.info("=" * 80 + "\n")
            
            # CRITICAL: Close and remove handler
            file_handler.close()
            gen_logger.removeHandler(file_handler)

            return GenerationResponse(
                success=True,
                message=f"Successfully generated Note {note_number} ({note_title}) for {company_name}",
                note_number=note_number,
                output_file=str(output_file),
                content=result,
            )

        except Exception as e:
            gen_logger.error("\n" + "=" * 80)
            gen_logger.error("❌ ERROR IN NOTE GENERATION")
            gen_logger.error("=" * 80)
            gen_logger.error(f"Note Number: {note_number}")
            gen_logger.error(f"Company: {company_name}")
            gen_logger.error(f"Error: {str(e)}")
            import traceback
            gen_logger.error(traceback.format_exc())
            gen_logger.error("=" * 80 + "\n")
            
            # Close and remove handler
            try:
                file_handler.close()
                gen_logger.removeHandler(file_handler)
            except:
                pass
            
            return GenerationResponse(
                success=False,
                message=f"Error generating note: {str(e)}",
                note_number=note_number,
            )
    @staticmethod
    async def batch_generate_notes(
        company_name: str, batch_id: str, category_id: Optional[str] = None
    ):
        """
        Public: Background task to generate notes for a company.

        Args:
            company_name: Name of the company
            batch_id: Unique batch identifier
            category_id: Optional category filter
        """
        logger.info("=" * 80)
        logger.info("🔄 STARTING BATCH NOTE GENERATION")
        logger.info("=" * 80)
        logger.info(f"Company: {company_name}")
        logger.info(f"Batch ID: {batch_id}")
        logger.info(f"Category Filter: {category_id or 'All categories'}")
        logger.info("=" * 80)
        
        try:
            companies = CompanyService.discover_companies()
            if company_name not in companies:
                logger.error(f"❌ Company not found: {company_name}")
                GenerationService.batch_status[batch_id].status = "failed"
                GenerationService.batch_status[batch_id].results.append(
                    GenerationResponse(
                        success=False, message=f"Company not found: {company_name}"
                    )
                )
                return

            # Get notes to generate
            if category_id:
                notes = companies[company_name]["notes_by_category"].get(
                    category_id, []
                )
                logger.info(f"📝 Generating {len(notes)} notes for category: {category_id}")
            else:
                notes = companies[company_name]["notes"]
                logger.info(f"📝 Generating all {len(notes)} notes")

            GenerationService.batch_status[batch_id].total_notes = len(notes)
            GenerationService.batch_status[batch_id].status = "running"

            for idx, note_info in enumerate(notes, 1):
                note_number = note_info["number"]
                logger.info(f"\n{'='*80}")
                logger.info(f"📝 Processing note {idx}/{len(notes)}: Note {note_number}")
                logger.info(f"{'='*80}")
                
                GenerationService.batch_status[batch_id].current_note = note_number

                result = GenerationService.generate_single_note(
                    company_name, note_number
                )
                GenerationService.batch_status[batch_id].results.append(result)
                GenerationService.batch_status[batch_id].completed_notes += 1
                
                if result.success:
                    logger.info(f"✅ Note {note_number} completed successfully")
                else:
                    logger.error(f"❌ Note {note_number} failed: {result.message}")

            GenerationService.batch_status[batch_id].status = "completed"
            GenerationService.batch_status[batch_id].current_note = None
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ BATCH GENERATION COMPLETED")
            logger.info("=" * 80)
            logger.info(f"Total notes: {len(notes)}")
            logger.info(f"Completed: {GenerationService.batch_status[batch_id].completed_notes}")
            logger.info("=" * 80 + "\n")

        except Exception as e:
            logger.error("\n" + "=" * 80)
            logger.error("❌ BATCH GENERATION FAILED")
            logger.error("=" * 80)
            logger.error(f"Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error("=" * 80 + "\n")
            
            GenerationService.batch_status[batch_id].status = "failed"
            GenerationService.batch_status[batch_id].results.append(
                GenerationResponse(
                    success=False, message=f"Batch generation failed: {str(e)}"
                )
            )

    @staticmethod
    def list_generated_notes(company_name: str, category_id: Optional[str] = None) -> list:
        """
        List all generated notes for a company, optionally filtered by category.

        Args:
            company_name: Name of the company
            category_id: Optional category ID to filter notes

        Returns:
            List of generated note files with metadata
        """
        logger.info(f"📋 Listing generated notes for {company_name}" + 
                   (f" (category: {category_id})" if category_id else ""))
        
        notes_dir = settings.get_entity_generated_notes_dir(company_name)

        if not notes_dir.exists():
            logger.warning(f"⚠️  Generated notes directory not found: {notes_dir}")
            return []

        # Get all markdown files
        note_files = list(notes_dir.glob("*.md"))
        logger.info(f"Found {len(note_files)} note files")

        # Get company info to access note titles from config
        companies = CompanyService.discover_companies()
        company_notes_map = {}
        if company_name in companies:
            # Build a map of note_number -> note_title from config
            for note_info in companies[company_name].get("notes", []):
                company_notes_map[note_info["number"]] = note_info["title"]

        # If category_id is provided, get the note numbers for that category
        category_notes = None
        if category_id:
            if company_name in companies:
                category_notes = companies[company_name].get("notes_by_category", {}).get(
                    category_id, []
                )
                category_note_numbers = {note["number"] for note in category_notes}

        result = []
        for file_path in note_files:
            # Extract note number from filename
            filename = file_path.name
            note_number = None

            # Try different patterns
            if filename.startswith("note"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    note_number = parts[0].replace("note", "")
            elif filename.startswith("Note_"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    note_number = parts[1]

            # If filtering by category, skip notes not in this category
            if category_notes is not None and note_number not in category_note_numbers:
                continue

            # Get file stats
            stats = file_path.stat()

            # Get title from config map
            title = company_notes_map.get(note_number)
            if not title:
                # Fallback: Read first few lines to get title from markdown
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read(500)
                        lines = content.split("\n")
                        for line in lines[:5]:
                            if line.startswith("# Note"):
                                title = line.strip("# ").strip()
                                break
                except:
                    pass

            result.append({
                "filename": filename,
                "file_path": str(file_path),
                "note_number": note_number,
                "title": title,
                "size_bytes": stats.st_size,
                "generated_at": stats.st_mtime,
                "download_url": f"/api/download-note/{company_name}/{filename}"
            })

        # Sort by modification time, newest first
        result.sort(key=lambda x: x["generated_at"], reverse=True)
        
        logger.info(f"✅ Returning {len(result)} notes")
        return result

    @staticmethod
    def get_note_content(company_name: str, filename: str) -> Optional[str]:
        """
        Get the content of a generated note file.

        Args:
            company_name: Name of the company
            filename: Name of the note file

        Returns:
            Note content as string or None if not found
        """
        logger.info(f"📄 Getting note content: {company_name}/{filename}")
        
        notes_dir = settings.get_entity_generated_notes_dir(company_name)
        file_path = notes_dir / filename

        if not file_path.exists() or not file_path.is_file():
            logger.warning(f"⚠️  Note file not found: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"✅ Note content retrieved ({len(content)} characters)")
            return content
        except Exception as e:
            logger.error(f"❌ Error reading note file {file_path}: {e}")
            return None
