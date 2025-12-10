"""
Financial Statement Service - Updated to include Balance Sheet generation
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from backend.services.path_service import PathService
from backend.services.pl_statement_service import PLStatementService
from backend.services.bs_statement_service import BSStatementService


class FinancialStatementService:
    """Service for generating financial statements and saving to correct directories"""

    STATEMENT_FILENAMES = {
        "profit-loss": "Profit_and_Loss_Statement.xlsx",
        "balance-sheet": "Balance_Sheet.xlsx",
        "cash-flow": "Cash_Flow_Statement.xlsx"
    }

    @staticmethod
    def get_statement_path(entity: str, statement_type: str) -> Path:
        """Get the file path for a financial statement"""
        path_service = PathService(entity)
        statements_dir = path_service.get_financial_statements_dir(entity)
        statements_dir.mkdir(parents=True, exist_ok=True)

        filename = FinancialStatementService.STATEMENT_FILENAMES.get(
            statement_type,
            f"{statement_type}.xlsx"
        )

        return statements_dir / filename

    @staticmethod
    def generate_profit_loss(
        entity: str,
        period_ended: str = None,
        note_numbers: List[str] = None
    ) -> Dict[str, Any]:
        """Generate Profit & Loss statement using existing service"""
        try:
            result = PLStatementService.generate_pl_statement(
                company_name=entity,
                period_ended=period_ended or datetime.now().strftime("%d %B %Y"),
                note_numbers=note_numbers
            )

            if result.success and result.output_file:
                return {
                    "success": True,
                    "message": "Profit & Loss statement generated successfully",
                    "statement_type": "profit-loss",
                    "output_file": result.output_file,
                    "entity": entity
                }
            else:
                return {
                    "success": False,
                    "error": result.message,
                    "statement_type": "profit-loss"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "statement_type": "profit-loss"
            }

    @staticmethod
    def generate_balance_sheet(
        entity: str,
        as_at_date: str = None,
        note_numbers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Balance Sheet using the new BS statement service
        
        Args:
            entity: Entity code
            as_at_date: Balance sheet date
            note_numbers: Optional list of note numbers to include

        Returns:
            Response dictionary with success status and file path
        """
        try:
            result = BSStatementService.generate_bs_statement(
                company_name=entity,
                as_at_date=as_at_date or datetime.now().strftime("%d %B %Y"),
                note_numbers=note_numbers
            )

            if result.success and result.output_file:
                return {
                    "success": True,
                    "message": "Balance Sheet generated successfully",
                    "statement_type": "balance-sheet",
                    "output_file": result.output_file,
                    "entity": entity
                }
            else:
                return {
                    "success": False,
                    "error": result.message,
                    "statement_type": "balance-sheet"
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "statement_type": "balance-sheet"
            }

    @staticmethod
    def generate_cash_flow(
        entity: str,
        period_ended: str = None,
        note_numbers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Cash Flow Statement (placeholder)
        
        Args:
            entity: Entity code
            period_ended: Period ending date
            note_numbers: Optional list of note numbers to include

        Returns:
            Response dictionary with success status and file path
        """
        try:
            path_service = PathService(entity)
            statements_dir = path_service.get_financial_statements_dir(entity)
            statements_dir.mkdir(parents=True, exist_ok=True)

            output_file = statements_dir / "Cash_Flow_Statement.xlsx"

            # TODO: Implement actual cash flow generation logic
            data = [
                {"Particulars": "Cash flow from operating activities", "Amount": ""},
                {"Particulars": "Cash flow from investing activities", "Amount": ""},
                {"Particulars": "Cash flow from financing activities", "Amount": ""},
                {"Particulars": "", "Amount": ""},
                {"Particulars": "Net increase/(decrease) in cash", "Amount": ""},
            ]

            df = pd.DataFrame(data)
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Cash Flow", index=False)

            print(f"✅ Cash Flow Statement saved to: {output_file}")

            return {
                "success": True,
                "message": "Cash Flow Statement generated successfully",
                "statement_type": "cash-flow",
                "output_file": str(output_file),
                "entity": entity
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "statement_type": "cash-flow"
            }

    @staticmethod
    def generate_all_statements(
        entity: str,
        period_ended: str = None,
        as_at_date: str = None
    ) -> Dict[str, Any]:
        """
        Generate all three financial statements
        
        Args:
            entity: Entity code
            period_ended: Period ending date (for P&L and Cash Flow)
            as_at_date: Balance sheet date

        Returns:
            Response dictionary with results for all statements
        """
        results = {
            "entity": entity,
            "statements": {}
        }

        # Generate P&L
        pl_result = FinancialStatementService.generate_profit_loss(entity, period_ended)
        results["statements"]["profit-loss"] = pl_result

        # Generate Balance Sheet
        bs_result = FinancialStatementService.generate_balance_sheet(entity, as_at_date)
        results["statements"]["balance-sheet"] = bs_result

        # Generate Cash Flow
        cf_result = FinancialStatementService.generate_cash_flow(entity, period_ended)
        results["statements"]["cash-flow"] = cf_result

        # Overall success
        results["success"] = all(
            r.get("success", False) for r in results["statements"].values()
        )

        return results

    @staticmethod
    def check_statement_readiness(entity: str) -> Dict[str, Any]:
        """
        Check readiness for all financial statements
        
        Args:
            entity: Entity code
            
        Returns:
            Dictionary with readiness status for each statement type
        """
        return {
            "entity": entity,
            "profit_loss": PLStatementService.check_pl_readiness(entity),
            "balance_sheet": BSStatementService.check_bs_readiness(entity),
            "cash_flow": {
                "is_ready": False,
                "message": "Cash Flow statement generation not yet implemented"
            }
        }