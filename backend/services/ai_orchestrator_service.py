"""
AI Orchestrator Service - Wraps the existing ai_orchestrator functionality
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from .path_service import PathService
from backend.config.period_config import period_config


class AIOrchestratorService:
    """Service for orchestrating AI-powered adjustments"""

    def __init__(self, entity: str = None):
        """
        Initialize AI Orchestrator Service

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

    async def process_all_adjustments(self, entity: str, processing_status: dict = None, processing_id: str = None) -> Dict[str, Any]:
        """Process all adjustments using the AI orchestrator
        
        Args:
            entity: Entity code
            processing_status: Optional dict to update with progress
            processing_id: Optional processing ID for status updates
        """
        self.set_entity(entity)

        try:
            # Update progress: Starting
            if processing_status and processing_id:
                processing_status[processing_id].progress = 20
                processing_status[processing_id].message = "Validating configuration and files..."

            # Change to the project root directory
            project_root = Path(__file__).parent.parent.parent
            os.chdir(project_root)

            # .env (ANTHROPIC_API_KEY) is optional now; consolidation does not require AI.
            # Proceed even if missing, only warn in logs.
            env_path = project_root / ".env"
            if not env_path.exists():
                print("⚠️  Warning: .env not found. Proceeding without ANTHROPIC_API_KEY (AI features disabled).")

            # Update progress: Running orchestrator
            if processing_status and processing_id:
                processing_status[processing_id].progress = 25
                processing_status[processing_id].message = "Starting AI orchestrator (this may take 3-5 minutes)..."
            
            print(f"🤖 Running AI orchestrator for {entity}...")

            # Run the AI orchestrator from backend/utils with entity parameter
            orchestrator_path = Path(__file__).parent.parent / "utils" / "ai_orchestrator.py"
            
            # Increase timeout to 10 minutes for complex entities
            result = subprocess.run(
                [sys.executable, str(orchestrator_path), entity],
                capture_output=True,
                text=True,
                cwd=project_root,
                env={
                    **os.environ,
                    'ENTITY': entity,
                    # Propagate selected period to subprocess
                    'PERIOD_KEY': period_config.get_current_period() or '',
                    'PERIOD_COLUMN': period_config.get_current_period_column(default="(Unaudited) Mar'25"),
                },
                timeout=600  # Increased to 10 minute timeout
            )

            # Log output for debugging
            print("=" * 80)
            print("AI Orchestrator STDOUT:")
            print(result.stdout)
            print("=" * 80)
            if result.stderr:
                print("AI Orchestrator STDERR:")
                print(result.stderr)
                print("=" * 80)

            # Update progress: Processing results
            if processing_status and processing_id:
                processing_status[processing_id].progress = 90
                processing_status[processing_id].message = "Validating output files..."

            if result.returncode == 0:
                # Check for output files
                output_files = self.check_output_files(entity)

                return {
                    "success": True,
                    "message": "All adjustments processed successfully",
                    "output_files": output_files,
                    "execution_time": 0,  # Could be calculated from logs
                    "adjustments": self.parse_adjustment_results(entity),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                error_msg = result.stderr or result.stdout or "Processing failed with no output"
                return {
                    "success": False,
                    "error": error_msg,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }

        except subprocess.TimeoutExpired:
            timeout_msg = "Processing timeout (exceeded 10 minutes). This usually means the AI service is taking too long or encountered an issue."
            print(f"⏱️ {timeout_msg}")
            return {
                "success": False,
                "error": timeout_msg
            }
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Exception in process_all_adjustments: {str(e)}")
            print(error_trace)
            return {
                "success": False,
                "error": f"{str(e)}\n{error_trace}"
            }

    def check_output_files(self, entity: str = None) -> List[str]:
        """Check which output files were created"""
        entity = entity or self.entity
        output_dir = self.path_service.get_adjusted_tb_dir(entity)

        # Only check for the final adjusted trial balance file
        # Individual reconciliation files are no longer generated
        expected_files = [
            "adjusted_trialbalance.xlsx"
        ]

        existing_files = []
        for file_name in expected_files:
            file_path = output_dir / file_name
            if file_path.exists():
                existing_files.append(str(file_path))

        return existing_files

    def parse_adjustment_results(self, entity: str = None) -> List[Dict[str, Any]]:
        """Parse adjustment results from JSON summary"""
        entity = entity or self.entity
        summary_path = self.path_service.get_adjusted_tb_dir(
            entity) / "ai_adjustment_summary.json"

        if summary_path.exists():
            try:
                with open(summary_path, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get('adjustments', [])
            except Exception as e:
                print(f"Error parsing adjustment results: {e}")
                return []
        return []

    async def generate_notes(self, entity: str, note_types: List[str]) -> Dict[str, Any]:
        """Generate financial notes"""
        self.set_entity(entity)

        try:
            # This would call the note generation functionality
            notes_dir = self.path_service.get_generated_notes_dir(entity)

            return {
                "success": True,
                "message": f"Generated {len(note_types)} notes for {entity}",
                "notes": note_types,
                "output_files": [],
                "output_directory": str(notes_dir)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_statements(self, entity: str, statement_types: List[str]) -> Dict[str, Any]:
        """Generate financial statements"""
        self.set_entity(entity)

        try:
            # This would call the statement generation functionality
            statements_dir = self.path_service.get_financial_statements_dir(entity)

            return {
                "success": True,
                "message": f"Generated {len(statement_types)} statements for {entity}",
                "statements": statement_types,
                "output_files": [],
                "output_directory": str(statements_dir)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_ai_insights(self, validation_data: Dict[str, Any]) -> str:
        """Get AI insights for validation results"""
        try:
            # Check if Anthropic API key is available
            import os

            from dotenv import load_dotenv
            load_dotenv()

            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                return "⚠️ AI Insights Not Available\n\nANTHROPIC_API_KEY is not configured. Please set your API key in the .env file to enable AI-powered insights."

            # Import the AI client
            from anthropic import Anthropic

            try:
                client = Anthropic(api_key=api_key)
            except Exception as client_error:
                return f"⚠️ AI Service Error\n\nFailed to initialize AI client: {str(client_error)}"

            # Create prompt for insights with validation data
            import json
            validation_data_str = json.dumps(validation_data, indent=2)

            prompt = f"""You are a financial accounting expert analyzing trial balance validation results.

VALIDATION DATA:
{validation_data_str}

Please provide comprehensive analysis including:
1. Executive Summary - Brief overview of the validation status
2. Why This Validation Matters - Explain the importance of each failed rule
3. Detailed Analysis of Failed Rules - Deep dive into each failure with specific examples
4. Priority Actions - Step-by-step recommendations ordered by urgency
5. Best Practices - Long-term recommendations to prevent future issues

Focus on actionable insights and be specific about the numbers and accounts involved.
Format your response with clear markdown headings and bullet points."""

            # Get model from environment
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            return f"⚠️ Error Generating AI Insights\n\nAn error occurred: {str(e)}\n\nPlease check your API configuration and try again."
