"""
Validation service for trial balance validation
"""

import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from .path_service import PathService


class ValidationService:
    """Service for validating trial balance data"""

    def __init__(self):
        # Add the parent directory to Python path
        parent_dir = Path(__file__).parent.parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.append(str(parent_dir))
        self.path_service = PathService()

    def _convert_to_native_types(self, obj):
        """Convert numpy types to native Python types recursively"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_to_native_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_native_types(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convert_to_native_types(item) for item in obj)
        else:
            return obj

    async def validate_trial_balance(self, file_path: str) -> Dict[str, Any]:
        """Validate uploaded trial balance file"""
        try:
            # Read the trial balance file
            df = pd.read_excel(file_path)

            # Basic validation rules
            checks = []

            # 1. Required columns
            required_cols = ["GL Code", "GL Code Description", "Mar'25"]
            missing = [c for c in required_cols if c not in [c.strip() for c in df.columns]]
            checks.append({
                "name": "Required columns present",
                "status": bool(len(missing) == 0),
                "details": missing
            })

            # 2. GL Code non-null
            if "GL Code" in df.columns:
                null_gl = df["GL Code"].isna().sum()
                checks.append({
                    "name": "No null GL Code",
                    "status": bool(null_gl == 0),
                    "details": int(null_gl)
                })

            # 3. Amounts numeric
            amount_col = "Mar'25" if "Mar'25" in df.columns else None
            if amount_col:
                non_num = pd.to_numeric(df[amount_col], errors="coerce").isna().sum()
                checks.append({
                    "name": "Amounts numeric",
                    "status": bool(non_num == 0),
                    "details": int(non_num)
                })

            # 4. Duplicates
            if "GL Code" in df.columns:
                dups = df["GL Code"].duplicated().sum()
                checks.append({
                    "name": "No duplicate GLs",
                    "status": bool(dups == 0),
                    "details": int(dups)
                })

            # 5. Balance near zero (tolerance 1.0)
            if amount_col:
                total = pd.to_numeric(df[amount_col], errors="coerce").fillna(0).sum()
                checks.append({
                    "name": "Balanced TB (~0)",
                    "status": bool(abs(total) < 1.0),
                    "details": float(total)
                })

            # 6. Invalid header names (trailing spaces)
            trailing = [c for c in df.columns if c != c.strip()]
            checks.append({
                "name": "No trailing spaces in headers",
                "status": bool(len(trailing) == 0),
                "details": trailing
            })

            # 7. Reasonable row count
            checks.append({
                "name": "Reasonable GL count (200-2000)",
                "status": bool(200 <= len(df) <= 2000),
                "details": int(len(df))
            })

            result = {
                "valid": bool(all(check["status"] for check in checks)),
                "checks": checks,
                "total_records": int(len(df)),
                "columns": list(df.columns)
            }

            return self._convert_to_native_types(result)

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "checks": []
            }

    async def validate_6_rules(self, entity: str, rule_overrides: Dict[str, bool] = None) -> Dict[str, Any]:
        """Validate trial balance against 6 rules using the existing validation module

        Args:
            entity: Entity code
            rule_overrides: Optional dict with rule override settings from frontend toggles
                           e.g., {"rule_1": True, "rule_2": False, ...}
        """
        try:
            # Import the validation module from backend.utils
            from backend.utils.tb_validate_7_rules import validate_final_trial_balance

            # Run validation with the specified entity and optional rule overrides
            success, message, output_file, summary = validate_final_trial_balance(
                entity=entity,
                rule_overrides=rule_overrides
            )

            if success:
                result = {
                    "success": True,
                    "message": "Validation completed successfully",
                    "rules_passed": summary.get('rules_passed', 0),
                    "rules_failed": summary.get('rules_failed', 0),
                    "total_rules": summary.get('total_rules_checked', 0),
                    "violations": summary.get('violations_count', {}),
                    "report_path": output_file,
                    "summary": summary,
                    "used_overrides": rule_overrides is not None
                }
                return self._convert_to_native_types(result)
            else:
                result = {
                    "success": False,
                    "message": message,
                    "rules_passed": 0,
                    "rules_failed": 0,
                    "total_rules": 0,
                    "violations": {},
                    "report_path": None
                }
                return self._convert_to_native_types(result)

        except Exception as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "rules_passed": 0,
                "rules_failed": 0,
                "total_rules": 0,
                "violations": {},
                "report_path": None
            }

    async def get_validation_summary(self, entity: str) -> Dict[str, Any]:
        """Get validation summary for an entity"""
        try:
            # Check if validation report exists in entity's output directory
            report_path = self.path_service.get_validation_report_path(entity)
            if not report_path.exists():
                return {
                    "has_report": False,
                    "message": "No validation report found"
                }

            # Read the report
            df = pd.read_excel(report_path)

            result = {
                "has_report": True,
                "total_records": len(df),
                "columns": list(df.columns),
                "report_path": str(report_path),
                "file_size": report_path.stat().st_size
            }

            return self._convert_to_native_types(result)

        except Exception as e:
            return {
                "has_report": False,
                "error": str(e)
            }

    async def check_acknowledgment_status(self, entity: str) -> Dict[str, Any]:
        """Check if validation exceptions have been acknowledged"""
        try:
            # Check for validation report
            report_path = self.path_service.get_validation_report_path(entity)
            
            if not report_path.exists():
                return {
                    "validation_exists": False,
                    "has_failures": False,
                    "is_acknowledged": False,
                    "can_proceed": True,  # No validation means no failures
                    "message": "No validation report found"
                }
            
            # Check for failed rules
            failed_details = await self.get_failed_rules_details(entity)
            
            if not failed_details.get('has_failures'):
                return {
                    "validation_exists": True,
                    "has_failures": False,
                    "is_acknowledged": False,  # No acknowledgment needed
                    "can_proceed": True,
                    "message": "All validation rules passed"
                }
            
            # Check for acknowledgment file
            acknowledgment_path = self.path_service.get_adjusted_tb_dir(
                entity) / "validation_acknowledgment.json"
            
            if acknowledgment_path.exists():
                import json
                with open(acknowledgment_path, 'r') as f:
                    acknowledgment = json.load(f)
                
                return {
                    "validation_exists": True,
                    "has_failures": True,
                    "is_acknowledged": True,
                    "can_proceed": True,
                    "acknowledgment": acknowledgment,
                    "message": "Validation exceptions acknowledged"
                }
            else:
                return {
                    "validation_exists": True,
                    "has_failures": True,
                    "is_acknowledged": False,
                    "can_proceed": False,
                    "failed_rules_count": failed_details.get('failed_rules_count', 0),
                    "message": "Validation exceptions require acknowledgment before proceeding"
                }
                
        except Exception as e:
            return {
                "validation_exists": False,
                "has_failures": False,
                "is_acknowledged": False,
                "can_proceed": False,
                "error": str(e),
                "message": f"Error checking acknowledgment status: {str(e)}"
            }

    async def get_failed_rules_details(self, entity: str) -> Dict[str, Any]:
        """Get detailed information about failed validation rules"""
        try:
            # Check if validation report exists
            report_path = self.path_service.get_validation_report_path(entity)
            
            if not report_path.exists():
                return {
                    "has_failures": False,
                    "message": "No validation report found. Please run validation first."
                }

            # Read the main validation report sheet
            df = pd.read_excel(report_path, sheet_name="Validation Report")
            
            # Parse the report to extract failed rules
            failed_rules = []
            current_rule = None
            
            for _, row in df.iterrows():
                section = str(row.get('Section', '')).strip()
                rule_name = str(row.get('Rule', '')).strip()
                metric = str(row.get('Metric', '')).strip()
                value = row.get('Value', '')
                status = str(row.get('Status', '')).strip()
                
                # Detect rule sections (RULE 1, RULE 2, etc.)
                if section.startswith('RULE') and rule_name and status:
                    current_rule = {
                        'rule_number': section,
                        'rule_name': rule_name,
                        'status': status,
                        'metrics': [],
                        'has_violations': False
                    }
                    
                    # Check if rule failed
                    if '✗ FAIL' in status or 'FAIL' in status:
                        failed_rules.append(current_rule)
                
                # Add metrics to current rule
                elif current_rule and section.startswith('RULE') and metric:
                    current_rule['metrics'].append({
                        'metric': metric,
                        'value': value
                    })
                    
                    # Check for violation details
                    if 'violation' in metric.lower() and 'sheet' in str(value).lower():
                        current_rule['has_violations'] = True
            
            result = {
                "has_failures": len(failed_rules) > 0,
                "failed_rules_count": len(failed_rules),
                "failed_rules": failed_rules,
                "report_path": str(report_path),
                "entity": entity
            }
            
            return self._convert_to_native_types(result)
            
        except Exception as e:
            return {
                "has_failures": False,
                "error": str(e),
                "message": f"Error reading validation report: {str(e)}"
            }
