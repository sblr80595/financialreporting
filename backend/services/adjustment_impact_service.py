"""
Adjustment Impact Analysis Service

Analyzes the impact of adjustments by reading the final trial balance file
which contains both unaudited and adjusted period columns.

Categorizes GL accounts by code prefix:
- 1xxx = Assets
- 2xxx = Liabilities  
- 3xxx = Equity
- 4xxx = Revenue
- 5xxx = Expenses
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


class AdjustmentImpactService:
    """Service for analyzing adjustment impacts on trial balance"""
    
    def __init__(self, entity: str):
        """Initialize service for specific entity"""
        self.entity = entity
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "data" / entity
        
        # Debug logging
        print(f"[AdjustmentImpactService] Initialized for entity: {entity}")
        print(f"[AdjustmentImpactService] Data directory: {self.data_dir}")
        print(f"[AdjustmentImpactService] Directory exists: {self.data_dir.exists()}")
        
    def classify_gl_by_code_prefix(self, gl_code: str) -> str:
        """
        Classify GL account by code prefix
        
        Args:
            gl_code: GL account code
            
        Returns:
            Category: 'Assets', 'Liabilities', 'Equity', 'Revenue', 'Expenses', 'Uncategorized'
        """
        if not gl_code:
            return 'Uncategorized'
        
        code_str = str(gl_code).strip()
        
        if not code_str:
            return 'Uncategorized'
        
        # Get first character
        first_char = code_str[0]
        
        if first_char == '1':
            return 'Assets'
        elif first_char == '2':
            return 'Liabilities'
        elif first_char == '3':
            return 'Equity'
        elif first_char == '4':
            return 'Revenue'
        elif first_char == '5':
            return 'Expenses'
        else:
            return 'Uncategorized'
    
    def detect_period_columns(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect unaudited and adjusted period columns from the dataframe
        
        Returns:
            Tuple of (unaudited_column, adjusted_column)
        """
        # Find numeric columns (excluding GL Code if it's numeric)
        period_cols = []
        for col in df.columns:
            col_str = str(col)
            col_lower = col_str.lower()
            
            # Skip GL Code and Description columns
            if 'gl code' in col_lower or 'gl_code' in col_lower or 'account code' in col_lower:
                continue
            if 'description' in col_lower or 'descri' in col_lower:
                continue
            
            # Check if column contains numeric data
            try:
                # Try to convert to numeric - if it works, it's a period column
                numeric_test = pd.to_numeric(df[col], errors='coerce')
                if not numeric_test.isna().all():  # If not all NaN, it's numeric
                    period_cols.append(col)
                    print(f"[AdjustmentImpactService] Found period column: {col}")
            except:
                continue
        
        if len(period_cols) < 1:
            print(f"[AdjustmentImpactService] Error: No period columns found")
            return (None, None)
        
        if len(period_cols) == 1:
            # If only one period column, treat it as both unaudited and adjusted
            print(f"[AdjustmentImpactService] Warning: Only one period column found, using as both unaudited and adjusted")
            return (period_cols[0], period_cols[0])
        
        # Look for unaudited/adjusted keywords in column names
        unaudited_col = None
        adjusted_col = None
        
        for col in period_cols:
            col_lower = str(col).lower()
            if 'unaudited' in col_lower or 'unadjusted' in col_lower:
                unaudited_col = col
            if 'adjusted' in col_lower or 'audited' in col_lower and 'unadjusted' not in col_lower and 'unaudited' not in col_lower:
                adjusted_col = col
        
        # If we found both through keywords, use them
        if unaudited_col and adjusted_col:
            print(f"[AdjustmentImpactService] Detected unaudited column: {unaudited_col}")
            print(f"[AdjustmentImpactService] Detected adjusted column: {adjusted_col}")
            return (unaudited_col, adjusted_col)
        
        # Otherwise, assume first is unaudited, last is adjusted
        unaudited_col = period_cols[0]
        adjusted_col = period_cols[-1]
        
        print(f"[AdjustmentImpactService] Detected unaudited column (first): {unaudited_col}")
        print(f"[AdjustmentImpactService] Detected adjusted column (last): {adjusted_col}")
        
        return (unaudited_col, adjusted_col)
    
    def analyze_impact(self) -> Dict:
        """
        Analyze adjustment impact by reading the final trial balance
        
        Returns:
            Dictionary with impact analysis results
        """
        try:
            # Read final trial balance (contains both unaudited and adjusted columns)
            # Note: final_trialbalance.xlsx contains the complete trial balance with all accounts
            final_tb_path = self.data_dir / "output" / "adjusted-trialbalance" / "final_trialbalance.xlsx"
            
            if not final_tb_path.exists():
                # Adjustments not yet applied
                return {
                    "entity": self.entity,
                    "status": "not_applied",
                    "message": "Adjustments have not been applied yet. Please apply adjustments first."
                }
            
            print(f"[AdjustmentImpactService] Reading final  trial balance: {final_tb_path}")
            
            # First, detect where the actual data starts (skip header rows)
            # Read first few rows to find the header row with "GL Code"
            test_df = pd.read_excel(final_tb_path, header=None, nrows=10)
            header_row = None
            for idx, row in test_df.iterrows():
                # Check if this row contains "GL Code" (case insensitive)
                row_vals = [str(val).lower() for val in row.values if pd.notna(val)]
                if any('gl code' in val or 'gl_code' in val for val in row_vals):
                    header_row = idx
                    print(f"[AdjustmentImpactService] Found header at row {idx}")
                    break
            
            # Read the Excel file with the correct header row
            if header_row is not None:
                df = pd.read_excel(final_tb_path, header=header_row, engine='openpyxl')
            else:
                # If no header row found, assume first row is header
                df = pd.read_excel(final_tb_path, engine='openpyxl')
            
            print(f"[AdjustmentImpactService] Loaded {len(df)} rows")
            print(f"[AdjustmentImpactService] Columns: {df.columns.tolist()}")
            
            # Standardize column names
            column_mapping = {}
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if col_lower in ['gl code', 'account code', 'gl_code', 'account_code', 'code']:
                    column_mapping[col] = 'GL Code'
                elif 'description' in col_lower or 'descri' in col_lower:
                    if 'GL Description' not in column_mapping.values():
                        column_mapping[col] = 'GL Description'
            
            df = df.rename(columns=column_mapping)
            
            # Ensure GL Code exists
            if 'GL Code' not in df.columns:
                raise ValueError("GL Code column not found in final trial balance")
            
            # Ensure GL Description exists
            if 'GL Description' not in df.columns:
                df['GL Description'] = ''
            
            # Detect period columns
            unaudited_col, adjusted_col = self.detect_period_columns(df)
            
            if not unaudited_col or not adjusted_col:
                raise ValueError("Could not detect unaudited and adjusted period columns")
            
            # Clean and prepare data
            df['GL Code'] = df['GL Code'].astype(str).str.strip()
            df['GL Description'] = df['GL Description'].fillna('').astype(str)
            
            # Remove empty rows
            df = df[df['GL Code'] != '']
            df = df[df['GL Code'] != 'nan']
            
            # Convert balance columns to numeric
            df['Unaudited Balance'] = pd.to_numeric(df[unaudited_col], errors='coerce').fillna(0)
            df['Adjusted Balance'] = pd.to_numeric(df[adjusted_col], errors='coerce').fillna(0)
            
            # Calculate change
            df['Change'] = df['Adjusted Balance'] - df['Unaudited Balance']
            
            # Classify accounts by GL code prefix
            df['Category'] = df['GL Code'].apply(self.classify_gl_by_code_prefix)
            
            # Identify uncategorized accounts
            uncategorized = df[df['Category'] == 'Uncategorized']
            if len(uncategorized) > 0:
                print(f"[AdjustmentImpactService] Warning: {len(uncategorized)} uncategorized accounts")
                print(f"[AdjustmentImpactService] Sample uncategorized codes: {uncategorized['GL Code'].head(10).tolist()}")
            
            # Calculate summary by category
            category_summary = {}
            for category in ['Assets', 'Liabilities', 'Equity', 'Revenue', 'Expenses']:
                cat_data = df[df['Category'] == category]
                category_summary[category] = {
                    'unaudited': float(cat_data['Unaudited Balance'].sum()),
                    'adjusted': float(cat_data['Adjusted Balance'].sum()),
                    'change': float(cat_data['Change'].sum()),
                    'count': len(cat_data)
                }
            
            # Identify material changes (>10% or >100,000)
            material_changes = []
            for _, row in df.iterrows():
                if row['Change'] == 0:
                    continue
                
                pct_change = 0
                if row['Unaudited Balance'] != 0:
                    pct_change = abs(row['Change'] / row['Unaudited Balance']) * 100
                
                if abs(row['Change']) > 100000 or pct_change > 10:
                    material_changes.append({
                        'gl_code': row['GL Code'],
                        'description': row['GL Description'],
                        'category': row['Category'],
                        'unaudited': float(row['Unaudited Balance']),
                        'adjusted': float(row['Adjusted Balance']),
                        'change': float(row['Change']),
                        'pct_change': float(pct_change) if pct_change > 0 else None
                    })
            
            # Sort material changes by absolute change
            material_changes.sort(key=lambda x: abs(x['change']), reverse=True)
            
            # GL-level changes (only non-zero changes)
            gl_changes = []
            for _, row in df[df['Change'] != 0].iterrows():
                gl_changes.append({
                    'gl_code': row['GL Code'],
                    'description': row['GL Description'],
                    'category': row['Category'],
                    'unaudited': float(row['Unaudited Balance']),
                    'adjusted': float(row['Adjusted Balance']),
                    'change': float(row['Change'])
                })
            
            # Uncategorized accounts exception report
            uncategorized_list = []
            if len(uncategorized) > 0:
                for _, row in uncategorized.iterrows():
                    uncategorized_list.append({
                        'gl_code': row['GL Code'],
                        'description': row['GL Description'],
                        'unaudited': float(row['Unaudited Balance']),
                        'adjusted': float(row['Adjusted Balance'])
                    })
            
            return {
                "entity": self.entity,
                "status": "success",
                "summary": {
                    "total_unaudited": float(df['Unaudited Balance'].sum()),
                    "total_adjusted": float(df['Adjusted Balance'].sum()),
                    "total_change": float(df['Change'].sum()),
                    "total_gl_codes": len(df),
                    "gl_codes_changed": len(df[df['Change'] != 0]),
                    "uncategorized_count": len(uncategorized)
                },
                "impact_by_category": category_summary,
                "material_changes": material_changes[:20],  # Top 20
                "gl_level_changes": gl_changes,  # All changes
                "uncategorized_accounts": uncategorized_list[:50],  # Up to 50 uncategorized
                "period_columns": {
                    "unaudited": unaudited_col,
                    "adjusted": adjusted_col
                }
            }
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[AdjustmentImpactService] Error: {error_detail}")
            return {
                "entity": self.entity,
                "status": "error",
                "message": str(e)
            }
