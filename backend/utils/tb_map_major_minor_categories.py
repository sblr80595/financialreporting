"""
Trial Balance Major/Minor Category Mapping
This script maps GL codes from the adjusted trial balance to their corresponding
major and minor categories from the reference mapping file.

Input:
- Adjusted Trial Balance: data/{entity}/output/adjusted-trialbalance/adjusted_trialbalance.xlsx
- Reference Mapping: data/{entity}/input/config/glcode_major_minor_mappings.xlsx

Output:
- Final Trial Balance with Categories: data/{entity}/output/adjusted-trialbalance/final_trial_balance.xlsx

Columns in output:
- GL Code
- GL Description
- BSPL
- Ind AS Major
- Ind AS Minor
- (Unaudited) Mar'25
- Mar'25 Adjusted
"""

import pandas as pd
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.utils.entity_paths import get_entity_paths


def _normalize_gl_code(series: pd.Series, keep_slash: bool = True) -> pd.Series:
    """Normalize GL codes consistently for merging without altering display values."""
    s = series.astype(str)
    s = s.str.replace("\u2019", "'", regex=False).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)
    pattern = r"[^0-9A-Za-z/]" if keep_slash else r"[^0-9A-Za-z]"
    s = s.str.replace(pattern, "", regex=True).str.lower()
    return s.where(~s.isin(['nan', 'none', 'null']), '')


def _normalize_desc(series: pd.Series) -> pd.Series:
    """Normalize descriptions for fallback joins."""
    s = series.astype(str)
    # Strip leading GL-code prefixes like "12015020 - " (regular hyphen or unicode dash)
    s = s.str.replace(r"^[0-9]+\s*[-\u2013\u2014]\s*", "", regex=True)
    s = s.str.replace("\u2019", "'", regex=False)
    s = s.str.replace("\u2018", "'", regex=False)
    s = s.str.replace("\u2013", "-", regex=False).str.replace("\u2014", "-", regex=False)
    s = s.str.lower().str.strip()
    s = s.str.replace(r"[^0-9a-z]+", " ", regex=True)
    s = s.str.replace(r"\s+", " ", regex=True).str.strip()
    return s.where(~s.isin(['nan', 'none', 'null']), '')


def map_categories(entity: str = "cpm"):
    """
    Main function to map major/minor categories to the adjusted trial balance.
    
    Args:
        entity: Entity code (e.g., 'cpm', 'hausen')
    
    Returns:
        tuple: (success: bool, message: str, output_file: str)
    """
    try:
        category_columns = ['BSPL', 'Ind AS Major', 'Ind AS Minor']

        # Get entity-specific paths
        paths = get_entity_paths(entity)
        
        source_file = str(paths["adjusted_tb_file"])
        reference_file = str(paths["mapping_file"])
        output_file = str(paths["final_tb_file"])
        
        # Check if source files exist
        if not os.path.exists(source_file):
            return False, f"❌ Source file not found: {source_file}", None
        
        if not os.path.exists(reference_file):
            return False, f"❌ Reference mapping file not found: {reference_file}", None
        
        print(f"📂 Processing entity: {entity.upper()}")
        print("📂 Reading adjusted trial balance...")
        # Read the adjusted trial balance
        df_adjusted_tb = pd.read_excel(source_file)
        print(f"✓ Loaded {len(df_adjusted_tb)} records from adjusted trial balance")
        
        print("📂 Reading GL code mapping reference...")
        # Read the reference mapping file
        df_mapping = pd.read_excel(reference_file)
        print(f"✓ Loaded {len(df_mapping)} records from mapping reference")
        
        # Clean column names (remove trailing spaces)
        df_mapping.columns = df_mapping.columns.str.strip()
        df_adjusted_tb.columns = df_adjusted_tb.columns.str.strip()
        
        # Ensure GL Code is in the same format for merging
        df_adjusted_tb['GL Code'] = df_adjusted_tb['GL Code'].astype(str).str.strip()
        df_mapping['GL Code'] = df_mapping['GL Code']
        # Normalize descriptions up front for fallback matching (use original mapping rows, even if GL Code is NaN)
        desc_col = next((c for c in df_mapping.columns if 'description' in c.lower()), None)
        df_mapping_all = df_mapping.copy()
        if desc_col:
            df_mapping_all[desc_col] = df_mapping_all[desc_col].astype(str).str.strip()
        df_adjusted_tb['__desc_norm'] = _normalize_desc(df_adjusted_tb.get('GL Description', ''))
        
        # Remove rows with NaN or empty GL Codes from mapping file (for code-based join),
        # but keep a separate copy for description-based join.
        df_mapping_code = df_mapping[df_mapping['GL Code'].notna() & (df_mapping['GL Code'] != '') & (df_mapping['GL Code'] != 'nan')].copy()
        df_mapping_code = df_mapping_code.drop_duplicates(subset=['GL Code'], keep='first')
        print(f"✓ Cleaned mapping file: {len(df_mapping_code)} unique GL Code mappings (code-based)")
        
        print("🔄 Mapping categories to GL codes...")
        # Perform left join to map categories
        # Select only needed columns from mapping
        mapping_columns = ['GL Code', 'BSPL', 'Ind AS Major', 'Ind AS Minor']
        
        # Verify required columns exist in mapping file
        missing_cols = [col for col in mapping_columns if col not in df_mapping.columns]
        if missing_cols:
            return False, f"❌ Missing required columns in mapping file: {', '.join(missing_cols)}", None
        
        df_mapping_subset = df_mapping_code[mapping_columns].copy()
        df_mapping_subset = df_mapping_subset.rename(columns={'GL Code': '_mapping_gl_code'})
        df_mapping_subset['__gl_norm'] = _normalize_gl_code(df_mapping_subset['_mapping_gl_code'], keep_slash=True)
        df_mapping_subset['__gl_norm_noslash'] = _normalize_gl_code(df_mapping_subset['_mapping_gl_code'], keep_slash=False)
        df_mapping_subset = df_mapping_subset.drop_duplicates(subset=['__gl_norm'], keep='first')
        # Prepare description-based mapping subset if available (use all mapping rows, including blank GL Codes)
        mapping_desc = None
        if desc_col:
            mapping_desc = df_mapping_all[[desc_col] + category_columns].copy()
            mapping_desc['__desc_norm'] = _normalize_desc(mapping_desc[desc_col])
            mapping_desc = mapping_desc.drop_duplicates(subset=['__desc_norm'], keep='first')

        # Add normalized keys to adjusted TB for a stable join without altering displayed GL Codes
        df_adjusted_tb['__gl_norm'] = _normalize_gl_code(df_adjusted_tb['GL Code'], keep_slash=True)
        df_adjusted_tb['__gl_norm_noslash'] = _normalize_gl_code(df_adjusted_tb['GL Code'], keep_slash=False)
        
        # Primary merge on exact slash-preserving key
        df_final = pd.merge(
            df_adjusted_tb,
            df_mapping_subset.drop(columns=['__gl_norm_noslash']),
            on='__gl_norm',
            how='left'
        )

        # Fallback: for unmapped rows, try a slash-stripped key to cover legacy adjusted TBs
        unmapped_mask = df_final[category_columns].isna().all(axis=1)
        if unmapped_mask.any():
            fallback_map = df_mapping_subset[['__gl_norm_noslash', '_mapping_gl_code'] + category_columns].drop_duplicates(subset=['__gl_norm_noslash'], keep='first')
            df_final = df_final.merge(
                fallback_map,
                left_on='__gl_norm_noslash',
                right_on='__gl_norm_noslash',
                how='left',
                suffixes=('', '_fallback')
            )
            for col in category_columns:
                df_final[col] = df_final[col].fillna(df_final[f"{col}_fallback"])
                df_final.drop(columns=[f"{col}_fallback"], inplace=True)
            if '_mapping_gl_code_fallback' in df_final.columns:
                df_final['_mapping_gl_code'] = df_final['_mapping_gl_code'].fillna(df_final['_mapping_gl_code_fallback'])
                df_final.drop(columns=['_mapping_gl_code_fallback'], inplace=True)

        # Restore formatted GL Codes as they appear in the mapping file (case and separators preserved)
        if '_mapping_gl_code' in df_final.columns:
            df_final['GL Code'] = df_final['_mapping_gl_code'].combine_first(df_final['GL Code'])
            df_final.drop(columns=['_mapping_gl_code'], inplace=True)

        # Fallback: use normalized description mapping for any rows still unmapped
        unmapped_mask = df_final[category_columns].isna().all(axis=1)
        if unmapped_mask.any() and mapping_desc is not None:
            df_final = df_final.merge(
                mapping_desc[['__desc_norm'] + category_columns],
                left_on='__desc_norm',
                right_on='__desc_norm',
                how='left',
                suffixes=('', '_desc')
            )
            for col in category_columns:
                df_final[col] = df_final[col].fillna(df_final[f"{col}_desc"])
                df_final.drop(columns=[f"{col}_desc"], inplace=True)
            df_final.drop(columns=['__desc_norm'], inplace=True, errors='ignore')
        else:
            df_final.drop(columns=['__desc_norm'], inplace=True, errors='ignore')

        df_final.drop(columns=['__gl_norm', '__gl_norm_noslash'], inplace=True, errors='ignore')
        
        # Dynamically detect period columns
        # Find columns matching patterns: "(Unaudited) {Month}'YY" and "{Month}'YY Adjusted"
        all_columns = df_final.columns.tolist()
        
        # Find the unaudited period column (contains "Unaudited" in parentheses)
        unaudited_col = None
        adjusted_col = None
        
        for col in all_columns:
            # Match pattern: "(Unaudited) Month'YY"
            if col.startswith('(Unaudited)') and "'" in col:
                unaudited_col = col
            # Match pattern: "Month'YY Adjusted" (must end with 'Adjusted')
            elif col.endswith('Adjusted') and "'" in col and 'Unaudited' not in col:
                adjusted_col = col
        
        # Validate that we found both columns
        if not unaudited_col or not adjusted_col:
            missing = []
            if not unaudited_col:
                missing.append("Unaudited period column (e.g., \"(Unaudited) Jun'25\")")
            if not adjusted_col:
                missing.append("Adjusted period column (e.g., \"Jun'25 Adjusted\")")
            
            error_msg = f"❌ Required columns not found in adjusted trial balance:\n"
            error_msg += f"   Missing: {', '.join(missing)}\n"
            error_msg += f"   Available columns: {', '.join(all_columns)}"
            return False, error_msg, None
        
        print(f"📊 Detected period columns:")
        print(f"   - Unaudited: '{unaudited_col}'")
        print(f"   - Adjusted: '{adjusted_col}'")
        
        # Reorder columns to match the required output format
        # Use the actual column names from the adjusted trial balance
        output_columns = [
            'GL Code',
            'GL Description',
            'BSPL',
            'Ind AS Major',
            'Ind AS Minor',
            unaudited_col,
            adjusted_col
        ]
        
        # Filter to only include columns that exist in df_final
        output_columns = [col for col in output_columns if col in df_final.columns]
        
        df_final = df_final[output_columns]
        
        # Check for unmapped GL codes
        unmapped_count = df_final['BSPL'].isna().sum()
        if unmapped_count > 0:
            print(f"⚠️ Warning: {unmapped_count} GL codes could not be mapped to categories")
            unmapped_codes = df_final[df_final['BSPL'].isna()]['GL Code'].tolist()
            print(f"   Unmapped GL Codes: {', '.join(unmapped_codes[:10])}")
            if len(unmapped_codes) > 10:
                print(f"   ... and {len(unmapped_codes) - 10} more")
        
        # Fill NaN values in category columns with empty strings
        # Keep numeric columns as numeric (NaN preserved)
        category_columns = ['BSPL', 'Ind AS Major', 'Ind AS Minor']
        for col in category_columns:
            if col in df_final.columns:
                df_final[col] = df_final[col].fillna('')
        
        print(f"💾 Saving final trial balance to {output_file}...")
        # Save to Excel (overwrite mode - delete existing file first if it exists)
        if os.path.exists(output_file):
            os.remove(output_file)
        df_final.to_excel(output_file, index=False, engine='openpyxl')
        
        # Create summary statistics
        total_records = len(df_final)
        mapped_records = len(df_final[df_final['BSPL'] != ''])
        mapping_percentage = (mapped_records / total_records * 100) if total_records > 0 else 0
        
        # Display preview of the output
        print("\n" + "="*70)
        print("📊 PREVIEW - First 10 Records from Final Trial Balance")
        print("="*70)
        preview_df = df_final.head(10)
        print(preview_df.to_string(index=False))
        
        success_message = f"""
✅ Category mapping completed successfully!

📊 Summary:
   • Total GL Codes: {total_records}
   • Successfully Mapped: {mapped_records}
   • Unmapped: {unmapped_count}
   • Mapping Rate: {mapping_percentage:.1f}%
   
📁 Output saved to: {output_file}

🎯 Next Step: Proceed to Step 5 - Validate 6 Rules
"""
        
        print(success_message)
        return True, success_message, output_file
        
    except Exception as e:
        error_message = f"❌ Error during category mapping: {str(e)}"
        print(error_message)
        import traceback
        traceback.print_exc()
        return False, error_message, None


def get_mapping_summary(output_file=None, entity="cpm"):
    """
    Get a summary of the mapping results for display purposes.
    
    Args:
        output_file (str): Path to the final trial balance file
        entity (str): Entity code (e.g., 'cpm', 'hausen')
        
    Returns:
        dict: Summary statistics and data preview
    """
    try:
        if output_file is None:
            paths = get_entity_paths(entity)
            output_file = str(paths["final_tb_file"])
        
        if not os.path.exists(output_file):
            return {
                'success': False,
                'message': 'Output file not found. Please run mapping first.'
            }
        
        df = pd.read_excel(output_file)
        
        # Calculate statistics
        total_records = len(df)
        mapped_records = len(df[df['BSPL'] != ''])
        unmapped_records = total_records - mapped_records
        
        # Get unique categories
        unique_bspl = df[df['BSPL'] != '']['BSPL'].nunique()
        unique_major = df[df['Ind AS Major'] != '']['Ind AS Major'].nunique()
        unique_minor = df[df['Ind AS Minor'] != '']['Ind AS Minor'].nunique()
        
        # Get sample data
        sample_data = df.head(10).to_dict('records')
        
        return {
            'success': True,
            'total_records': total_records,
            'mapped_records': mapped_records,
            'unmapped_records': unmapped_records,
            'unique_bspl': unique_bspl,
            'unique_major': unique_major,
            'unique_minor': unique_minor,
            'sample_data': sample_data,
            'file_path': output_file
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error reading mapping results: {str(e)}'
        }


if __name__ == "__main__":
    """
    Execute category mapping when script is run directly.
    """
    import sys
    
    # Get entity from command line or use default
    entity = sys.argv[1] if len(sys.argv) > 1 else "cpm"
    
    print("=" * 70)
    print("🗂️  Trial Balance Category Mapping")
    print(f"📊 Entity: {entity.upper()}")
    print("=" * 70)
    print()
    
    success, message, output_file = map_categories(entity)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ MAPPING COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n📁 Output file: {output_file}")
        print("\n💡 You can now:")
        print("   1. View the output file in Excel")
        print("   2. Download the file from the output folder")
        print("   3. Proceed to Step 5: Validate 6 Rules")
    else:
        print("\n" + "=" * 70)
        print("❌ MAPPING FAILED")
        print("=" * 70)
        print(f"\n{message}")
