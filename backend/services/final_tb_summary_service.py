"""
Final Trial Balance Summary Service

Analyzes the final trial balance file and provides summary statistics by:
- BSPL categories (BS vs PL)
- Ind AS Major categories (dynamic)
- Unaudited vs Adjusted comparisons
"""

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class FinalTrialBalanceSummaryService:
    """Service for analyzing final trial balance with BSPL and Ind AS categorization"""
    
    def __init__(self, entity: str):
        """Initialize service for specific entity"""
        self.entity = entity
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "data" / entity
        
        # Debug logging
        print(f"[FinalTBSummaryService] Initialized for entity: {entity}")
        print(f"[FinalTBSummaryService] Data directory: {self.data_dir}")
    
    def find_final_tb_file(self) -> Optional[Path]:
        """
        Automatically find the final trial balance file in the output folder
        Looks for any Excel file in adjusted-trialbalance output folder
        """
        output_dir = self.data_dir / "output" / "adjusted-trialbalance"
        
        if not output_dir.exists():
            return None
        
        # Look for any Excel file
        excel_files = []
        for ext in ['*.xlsx', '*.xls', '*.xlsb']:
            excel_files.extend(list(output_dir.glob(ext)))
        
        if not excel_files:
            return None
        
        # Prefer files with "final" in the name
        final_files = [f for f in excel_files if 'final' in f.name.lower()]
        if final_files:
            print(f"[FinalTBSummaryService] Found final TB: {final_files[0].name}")
            return final_files[0]
        
        # Otherwise use the first Excel file
        print(f"[FinalTBSummaryService] Using TB file: {excel_files[0].name}")
        return excel_files[0]
    
    def detect_period_columns(self, df: pd.DataFrame) -> tuple:
        """
        Detect the unaudited and adjusted column names
        Returns: (unaudited_col, adjusted_col)
        """
        unaudited_col = None
        adjusted_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            # Look for unaudited column
            if 'unaudited' in col_lower and not unaudited_col:
                unaudited_col = col
            
            # Look for adjusted column (but not "unadjusted")
            if 'adjusted' in col_lower and 'unadjusted' not in col_lower and not adjusted_col:
                adjusted_col = col
        
        return unaudited_col, adjusted_col
    
    def analyze_final_tb(self) -> Dict:
        """
        Main analysis method
        
        Returns:
            Dictionary with summary statistics by BSPL and Ind AS Major categories
        """
        try:
            # Find the final trial balance file
            tb_file = self.find_final_tb_file()
            
            if not tb_file:
                return {
                    "entity": self.entity,
                    "status": "not_found",
                    "message": "Final trial balance file not found. Please complete Step 4 category mapping first."
                }
            
            # Read the Excel file
            df = pd.read_excel(tb_file, engine='openpyxl')
            
            print(f"[FinalTBSummaryService] Loaded {len(df)} rows from {tb_file.name}")
            print(f"[FinalTBSummaryService] Columns: {df.columns.tolist()}")
            
            # Detect period columns
            unaudited_col, adjusted_col = self.detect_period_columns(df)
            
            if not unaudited_col or not adjusted_col:
                return {
                    "entity": self.entity,
                    "status": "error",
                    "message": f"Could not find unaudited and adjusted columns. Available columns: {df.columns.tolist()}"
                }
            
            print(f"[FinalTBSummaryService] Unaudited column: {unaudited_col}")
            print(f"[FinalTBSummaryService] Adjusted column: {adjusted_col}")
            
            # Ensure numeric columns
            df[unaudited_col] = pd.to_numeric(df[unaudited_col], errors='coerce').fillna(0)
            df[adjusted_col] = pd.to_numeric(df[adjusted_col], errors='coerce').fillna(0)
            
            # Calculate change
            df['Change'] = df[adjusted_col] - df[unaudited_col]
            
            # Overall summary
            total_summary = {
                "total_unaudited": float(df[unaudited_col].sum()),
                "total_adjusted": float(df[adjusted_col].sum()),
                "total_change": float(df['Change'].sum()),
                "total_accounts": len(df)
            }
            
            # BSPL summary
            bspl_summary = self.get_bspl_summary(df, unaudited_col, adjusted_col)
            
            # Ind AS Major summary
            indas_major_summary = self.get_indas_major_summary(df, unaudited_col, adjusted_col)
            
            return {
                "entity": self.entity,
                "status": "success",
                "file_name": tb_file.name,
                "summary": total_summary,
                "bspl_summary": bspl_summary,
                "indas_major_summary": indas_major_summary,
                "period_columns": {
                    "unaudited": unaudited_col,
                    "adjusted": adjusted_col
                }
            }
            
        except Exception as e:
            print(f"[FinalTBSummaryService] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "entity": self.entity,
                "status": "error",
                "message": str(e)
            }
    
    def get_bspl_summary(self, df: pd.DataFrame, unaudited_col: str, adjusted_col: str) -> Dict:
        """
        Get summary by BSPL category (BS vs PL)
        """
        if 'BSPL' not in df.columns:
            return {}
        
        summary = {}
        
        for bspl_cat in df['BSPL'].unique():
            if pd.isna(bspl_cat):
                continue
            
            cat_data = df[df['BSPL'] == bspl_cat]
            
            summary[str(bspl_cat)] = {
                "unaudited": float(cat_data[unaudited_col].sum()),
                "adjusted": float(cat_data[adjusted_col].sum()),
                "change": float(cat_data['Change'].sum()),
                "count": len(cat_data)
            }
        
        return summary
    
    def get_indas_major_summary(self, df: pd.DataFrame, unaudited_col: str, adjusted_col: str) -> List[Dict]:
        """
        Get summary by Ind AS Major category (dynamic categories)
        Includes GL-level details for each category
        """
        if 'Ind AS Major' not in df.columns:
            return []
        
        summary = []
        
        # Get unique categories (excluding NaN)
        categories = df['Ind AS Major'].dropna().unique()
        
        for category in sorted(categories):
            cat_data = df[df['Ind AS Major'] == category].copy()
            
            # Get GL-level changes for this category (only accounts with changes)
            gl_changes = []
            for _, row in cat_data[cat_data['Change'] != 0].iterrows():
                gl_changes.append({
                    'gl_code': str(row.get('GL Code', '')),
                    'description': str(row.get('GL Description', '')),
                    'unaudited': float(row[unaudited_col]),
                    'adjusted': float(row[adjusted_col]),
                    'change': float(row['Change'])
                })
            
            summary.append({
                "category": str(category),
                "unaudited": float(cat_data[unaudited_col].sum()),
                "adjusted": float(cat_data[adjusted_col].sum()),
                "change": float(cat_data['Change'].sum()),
                "count": len(cat_data),
                "changed_count": len(cat_data[cat_data['Change'] != 0]),
                "gl_changes": gl_changes  # Include GL-level data
            })
        
        # Sort by absolute change (largest changes first)
        summary.sort(key=lambda x: abs(x['change']), reverse=True)
        
        return summary
