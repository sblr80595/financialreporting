"""
ADJUSTED TRIAL BALANCE GENERATOR
=================================

This script generates the adjusted trial balance by:
1. Loading the source unadjusted_trialbalance.xlsx (3 columns: GL Code, GL Description, (Unaudited) Mar'25)
2. Loading each of the 6 adjustment reconciliation files
3. Matching GL Codes and extracting adjustment values
4. Creating output with structure:
   - First 3 columns from unadjusted_trialbalance.xlsx
   - 6 adjustment columns (Adj1_ENC, Adj2_RB, Adj3_RF, Adj4_INTERCO, Adj5_GT, Adj6_RECLASS)
   - Final column: Mar'25 Adjusted (rounded to 2 decimals)
5. Saving to data/{entity}/output/adjusted-trialbalance/adjusted_trialbalance.xlsx

Usage:
    python generate_consolidate_tb.py [entity]
    
    entity: Optional entity code (e.g., 'cpm', 'hausen'). Defaults to 'cpm' if not provided.
    
Returns:
    True if successful, False otherwise
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import entity configuration for proper normalization
from backend.config.entities import EntityConfig
from backend.config.period_config import period_config

# Get entity from command line argument or environment variable, default to 'cpm'
raw_entity = sys.argv[1] if len(sys.argv) > 1 else os.getenv('ENTITY', 'cpm')
ENTITY = EntityConfig.normalize_entity_code(raw_entity)  # Properly normalize entity code

# Set up paths based on entity
DATA_DIR = Path(__file__).parent.parent.parent / "data" / ENTITY
SOURCE_FILES_DIR = DATA_DIR / "input" / "unadjusted-trialbalance"
CONFIG_DIR = DATA_DIR / "input" / "config"
OUTPUT_FILES_DIR = DATA_DIR / "output" / "adjusted-trialbalance"

# Ensure output directory exists
OUTPUT_FILES_DIR.mkdir(parents=True, exist_ok=True)

# Apply period passed via environment so this separate process uses UI selection
_ENV_PERIOD_KEY = os.getenv('PERIOD_KEY', '').strip()
_ENV_PERIOD_COLUMN = os.getenv('PERIOD_COLUMN', '').strip()
try:
    if _ENV_PERIOD_KEY:
        period_config.set_period(_ENV_PERIOD_KEY)
    elif _ENV_PERIOD_COLUMN:
        period_config.set_period_column(_ENV_PERIOD_COLUMN)
except Exception:
    # continue with defaults if anything goes wrong
    pass


def _normalize_gl_code(series: pd.Series, *, allow_slash: bool = None) -> pd.Series:
    """Normalize GL Code values for reliable joins.

    - Convert to string and trim whitespace
    - Remove leading apostrophes added by Excel (e.g., '11201010)
    - Remove trailing .0 from numeric imports (e.g., 11201010.0)
    - Optionally keep '/' for entities that rely on it (all except CPM Malaysia)
    - Remove other punctuation/whitespace to stabilise joins
    - Lowercase (no-op for digits, but keeps consistent behavior)
    """
    if allow_slash is None:
        allow_slash = EntityConfig.normalize_entity_code(ENTITY) != "cpm"

    # Convert to string and basic trim
    s = series.astype(str).str.strip()

    # Normalize unicode whitespace and apostrophes
    s = s.str.replace("\u2019", "'", regex=False)  # curly to straight apostrophe
    s = s.str.lstrip("'")  # remove leading apostrophes from Excel text formatting

    # Remove trailing .0 artifacts from float-looking strings
    s = s.str.replace(r"\.0$", "", regex=True)

    # Keep only letters/digits and optionally slash; remove other punctuation/spaces
    pattern = r"[^0-9A-Za-z/]" if allow_slash else r"[^0-9A-Za-z]"
    s = s.str.replace(pattern, "", regex=True)

    # Lowercase for consistency (digits unaffected)
    s = s.str.lower()

    # Convert placeholders to blank
    s = s.where(~s.isin(['nan', 'none', 'null']), '')
    return s


def _to_numeric(series: pd.Series) -> pd.Series:
    """Robust numeric parser for amounts.

    Handles:
    - Commas as thousand separators
    - Parentheses for negatives: (123.45) -> -123.45
    - Unicode minus U+2212 converted to ASCII '-'
    - Leading/trailing spaces and stray apostrophes
    """
    s = series.astype(str)
    # Normalize unicode minus and apostrophes
    s = s.str.replace("\u2212", "-", regex=False)  # unicode minus to hyphen-minus
    s = s.str.replace("\u2019", "'", regex=False)
    s = s.str.strip().str.lstrip("'")
    # Parentheses negatives
    neg_mask = s.str.match(r"^\(.*\)$")
    s = s.str.replace(r"[(),]", "", regex=True)
    # Now to numeric
    out = pd.to_numeric(s, errors='coerce').fillna(0.0)
    out[neg_mask] = -out[neg_mask]
    return out


def _normalize_desc(series: pd.Series) -> pd.Series:
    """Normalize description strings for robust matching across files.

    - Convert to string, lowercase
    - Normalize curly quotes and unicode dashes
    - Remove punctuation and collapse to alphanumerics + spaces
    - Collapse multiple spaces and trim
    """
    s = series.astype(str)
    s = s.str.replace("\u2019", "'", regex=False)
    s = s.str.replace("\u2018", "'", regex=False)
    s = s.str.replace("\u2013", "-", regex=False).str.replace("\u2014", "-", regex=False)
    s = s.str.lower().str.strip()
    # Remove all non-alphanumeric characters (keep spaces)
    s = s.str.replace(r"[^0-9a-z]+", " ", regex=True)
    # Collapse multiple spaces
    s = s.str.replace(r"\s+", " ", regex=True).str.strip()
    # Treat placeholders as blank
    s = s.where(~s.isin(['nan', 'none', 'null']), '')
    return s


def _load_desc_mapping():
    """Load optional description remapping rules for this entity.

    Path: data/{entity}/input/config/adjustment_description_map.json
    Format: { "from": "to", ... } using raw strings (before normalization).
    Returns a dict keyed by normalized source description to target raw string.
    """
    try:
        import json
        mapping_path = CONFIG_DIR / 'adjustment_description_map.json'
        if mapping_path.exists():
            with open(mapping_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                norm = {}
                for k, v in raw.items():
                    try:
                        nk = _normalize_desc(pd.Series([k])).iloc[0]
                        norm[nk] = str(v)
                    except Exception:
                        continue
                print(f" Loaded description mapping: {len(norm)} rule(s) from {mapping_path}")
                return norm
    except Exception as e:
        print(f"  Could not load description mapping: {e}")
    return {}


def _guess_desc_amount_columns(df: pd.DataFrame):
    """Heuristically guess description and amount columns from a dataframe
    that lacks explicit 'GL Code' and clear headers.

    Returns (desc_col, amount_col) or (None, None) if not confident.
    """
    if df is None or df.empty:
        return None, None

    cols = list(df.columns)
    # Pre-normalized name map
    name_map = {c: str(c).strip() for c in cols}
    lower_map = {c: name.lower() for c, name in name_map.items()}

    # Quick matches by name
    desc_hints = ['description', 'gl description', 'gl code description', 'account name', 'account description', 'particulars', 'details', 'narration']
    amount_hints = ['amount', 'value', 'adjustment', 'adjusted value', 'total adjusted value', 'debit', 'credit', 'dr', 'cr', 'impact']

    desc_col = None
    amount_col = None

    # Prefer explicit name hints
    for c, l in lower_map.items():
        if any(h in l for h in desc_hints) and not l.startswith('unnamed'):
            desc_col = c
            break
    for c, l in lower_map.items():
        if any(h in l for h in amount_hints) and not l.startswith('unnamed'):
            amount_col = c
            break

    # If still missing, infer by content profile
    def _numeric_ratio(series):
        s = pd.to_numeric(series, errors='coerce')
        return float(s.notna().mean())

    def _text_ratio(series):
        s = series.astype(str)
        s = s.where(~s.isin(['nan', 'None', 'NaN']), '')
        return float((s.str.strip() != '').mean())

    if desc_col is None or amount_col is None:
        # Score columns
        numeric_scores = {}
        text_scores = {}
        for c in cols:
            l = lower_map[c]
            if l.startswith('unnamed'):
                continue
            try:
                numeric_scores[c] = _numeric_ratio(df[c])
            except Exception:
                numeric_scores[c] = 0.0
            try:
                text_scores[c] = _text_ratio(df[c])
            except Exception:
                text_scores[c] = 0.0

        # Choose the most text-rich column as description
        if desc_col is None and text_scores:
            desc_col = max(text_scores, key=lambda c: (text_scores[c], 0 if any(h in lower_map[c] for h in desc_hints) else -1))
        # Choose the most numeric column as amount
        if amount_col is None and numeric_scores:
            amount_col = max(numeric_scores, key=lambda c: (numeric_scores[c], 0 if any(h in lower_map[c] for h in amount_hints) else -1))

        # Sanity thresholds: require at least some text and numeric confidence
        if desc_col and text_scores.get(desc_col, 0) < 0.4:
            desc_col = None
        if amount_col and numeric_scores.get(amount_col, 0) < 0.4:
            amount_col = None

    return desc_col, amount_col


def load_trial_balance():
    """Load the source unadjusted trial balance and summarize by GL Code.

    Be flexible about the input filename. Prefer `unadjusted_trialbalance.xlsx`,
    but if it doesn't exist, search the unadjusted-trialbalance folder for a
    reasonable Excel file to use (names containing 'trial' or 'balance' first,
    otherwise the first .xlsx/.xls file).
    """
    preferred = SOURCE_FILES_DIR / "unadjusted_trialbalance.xlsx"

    # Resolve trial balance path with fallbacks
    if preferred.exists():
        tb_path = preferred
    else:
        candidates = []
        # Priority 1: files containing 'trial' or 'balance'
        for ext in ("*.xlsx", "*.xls"):
            for p in SOURCE_FILES_DIR.glob(ext):
                name = p.name.lower()
                if "trial" in name or "balance" in name:
                    candidates.append(p)
        # Priority 2: any excel file
        if not candidates:
            candidates = list(SOURCE_FILES_DIR.glob("*.xlsx")) + list(SOURCE_FILES_DIR.glob("*.xls"))

        if candidates:
            tb_path = sorted(candidates)[0]
            print(f"  Preferred file not found. Using: {tb_path}")
        else:
            print(f" Trial Balance file not found in: {SOURCE_FILES_DIR}")
            print("   Expected 'unadjusted_trialbalance.xlsx' or any Excel file containing 'trial'/'balance'.")
            return None
    
    try:
        # Try to sniff header row if TB has preface rows
        header_row = 0
        try:
            peek = pd.read_excel(tb_path, header=None, nrows=10)
            for r in range(min(10, len(peek))):
                row_vals = [str(v).strip().lower() for v in list(peek.iloc[r].values)]
                row_text = " ".join(row_vals)
                if ('gl' in row_text and ('code' in row_text or 'number' in row_text or 'account' in row_text)):
                    header_row = r
                    break
        except Exception:
            header_row = 0

        df = pd.read_excel(tb_path, header=header_row)
        
        # Expected columns: GL Code, GL Description, (Unaudited) Mar'25
        print(f" Loaded Trial Balance with {len(df)} transaction rows")
        print(f"   Columns: {df.columns.tolist()}")
        
        # Normalize GL Code for matching
        df['GL Code'] = _normalize_gl_code(df['GL Code'])
        
        # Normalize column names - handle variations like "GL Description" or "GL Code Description "
        # Find the description column (could be "GL Description" or "GL Code Description " or similar)
        desc_col = None
        for col in df.columns:
            col_l = str(col).lower()
            if 'description' in col_l and 'gl' in col_l:
                desc_col = col
                break
        
        if desc_col is None:
            print(f" Could not find GL description column in: {df.columns.tolist()}")
            return None
        
        # Determine the amount column to use (driven by selected period)
        amount_col = None
        lower_map = {c: str(c).lower() for c in df.columns}
        # prioritize period-driven names
        period_candidates, short_label = _derive_period_labels()
        preferred_names = [s.lower() for s in period_candidates] + [
            "closing balance", "closing_balance", "balance",
            "amount", "net amount", "net_amount"
        ]
        for pref in preferred_names:
            for col in df.columns:
                if lower_map[col].strip() == pref:
                    amount_col = col
                    break
            if amount_col:
                break
        # fallback: any column containing month hint or amount-like
        if amount_col is None:
            for col in df.columns:
                l = lower_map[col]
                if ("mar" in l and "25" in l) or ("unaudited" in l and ("mar" in l or "balance" in l)):
                    amount_col = col
                    break
        # final fallback: last numeric column
        if amount_col is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist() if 'np' in globals() else []
            # Import numpy locally if not present
            if not numeric_cols:
                try:
                    import numpy as _np
                    numeric_cols = df.select_dtypes(include=[_np.number]).columns.tolist()
                except Exception:
                    numeric_cols = []
            if numeric_cols:
                amount_col = numeric_cols[-1]
        
        if amount_col is None:
            print(f" Could not identify amount column in TB. Columns: {df.columns.tolist()}")
            return None

        # Prepare rows exactly as in TB (do not aggregate away rows)
        print(f"   Preparing rows without collapsing duplicates...")
        print(f"   Using description column: '{desc_col}'")
        # If the detected amount column itself carries a month label, use it to override short_label
        try:
            header = amount_col.replace("\u2019", "'")  # normalize curly quote
            import re
            # Look for patterns like (Unaudited) Jun'25 or Jun'25
            m = re.search(r"([A-Za-z]{3})\'?\s*(\d{2})", header)
            if m:
                mo = m.group(1).title()
                yr = m.group(2)
                short_label = f"{mo}'{yr}"
        except Exception:
            pass

        print(f"   Using amount column: '{amount_col}'")
        
        # Ensure amount column numeric (robust parse)
        df[amount_col] = _to_numeric(df[amount_col])

        # Keep the TB as-is (no grouping), just select and rename columns
        df_grouped = df[[
            'GL Code',
            desc_col,
            amount_col
        ]].copy()
        
        # Rename the description column to standardized name
        df_grouped.rename(columns={desc_col: 'GL Description', amount_col: f"(Unaudited) {short_label}"}, inplace=True)
        
        # Store chosen period label globally for later output column naming
        global _SHORT_PERIOD_LABEL
        _SHORT_PERIOD_LABEL = short_label
        
        print(f" Prepared {len(df_grouped)} TB rows")
        
        # Ensure blank GL Codes are truly blank (not the string 'nan')
        df_grouped['GL Code'] = df_grouped['GL Code'].replace({'nan': ''})

        return df_grouped
        
    except Exception as e:
        print(f" Error loading Trial Balance: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_adjustment_from_manual_file(filename, adj_column_name):
    """
    Load adjustments directly from manual adjustment file (no reconciliation file needed)
    
    Args:
        filename: Name of the manual adjustment file (e.g., 'enc_correct_period_adjustments.xlsx')
        adj_column_name: Expected adjustment column name (e.g., 'Adj1_ENC')
    
    Returns:
        DataFrame with GL Code and adjustment column, or None if file not found
    """
    # First try to find in manual-adjustments directory
    manual_dir = DATA_DIR / "input" / "manual-adjustments"
    filepath = manual_dir / filename
    
    if not filepath.exists():
        print(f"  Manual adjustment file not found: {filepath}")
        print(f"   Filling with zeros for {adj_column_name}")
        return None
    
    try:
        # Robust header detection: try multiple header rows and pick the best by content profile
        candidate_headers = [0, 1, 2, 3]
        best = None
        best_score = -1
        for hr in candidate_headers:
            try:
                tmp = pd.read_excel(filepath, header=hr)
                dcol, acol = _guess_desc_amount_columns(tmp)
                # score by numeric/text ratio and number of valid rows
                if dcol and acol:
                    try:
                        numeric_ratio = pd.to_numeric(tmp[acol], errors='coerce').notna().mean()
                    except Exception:
                        numeric_ratio = 0.0
                    try:
                        text_ratio = tmp[dcol].astype(str).str.strip().replace({'nan': ''}).ne('').mean()
                    except Exception:
                        text_ratio = 0.0
                    valid_rows = 0
                    try:
                        tt = tmp[[dcol, acol]].copy()
                        tt[dcol] = tt[dcol].astype(str).str.strip()
                        tt[acol] = pd.to_numeric(tt[acol], errors='coerce')
                        valid_rows = int(((tt[dcol] != '') & tt[acol].notna()).sum())
                    except Exception:
                        valid_rows = 0
                    score = numeric_ratio + text_ratio + min(1.0, valid_rows / 3.0)
                    if score > best_score:
                        best_score = score
                        best = (hr, tmp)
            except Exception:
                continue

        if best is not None and best_score >= 1.2:
            header_row = best[0]
            df = best[1]
        else:
            # Fallback to simple header=0
            header_row = 0
            df = pd.read_excel(filepath, header=header_row)
        
        # Expected columns vary, but we need GL Code and some amount/adjustment column
        # Common patterns: 'GL Code', 'GL_Code', 'GLCode'
        gl_code_col = None
        gl_synonyms = [
            ('gl', 'code'), ('gl', 'number'), ('gl', 'no'), ('gl', 'id'),
            ('account', 'code'), ('account', 'number'), ('acc', 'code'), ('acc', 'no')
        ]
        cols_lower_map = {c: str(c).lower().strip() for c in df.columns}
        for col, lower in cols_lower_map.items():
            # Avoid mis-detecting description columns such as
            # "GL Code Description" as GL Code identifiers.
            if 'desc' in lower or 'description' in lower:
                continue
            for a, b in gl_synonyms:
                if a in lower and b in lower:
                    gl_code_col = col
                    break
            if gl_code_col:
                break

        # If the detected GL Code column has no real variation
        # (e.g., a single repeated placeholder or mostly blanks),
        # treat it as unusable and fall back to description-based logic.
        if gl_code_col is not None:
            try:
                gl_series = _normalize_gl_code(df[gl_code_col])
                non_empty = gl_series[gl_series != ""]
                if non_empty.nunique() < 2:
                    gl_code_col = None
            except Exception:
                gl_code_col = None
        
        if gl_code_col is None:
            # Try description-based fallback
            desc_col = None
            desc_synonyms = [
                'gl description', 'gl code description', 'description', 'account description', 'account name', 'gl name', 'gl account'
            ]
            for col, lower in cols_lower_map.items():
                if any(s in lower for s in desc_synonyms):
                    desc_col = col
                    break

            # If no explicit description column, attempt header-as-data fallback.
            if desc_col is None:
                str_headers = [
                    c for c in df.columns
                    if isinstance(c, str) and not str(c).lower().startswith('unnamed') and str(c).strip() != ''
                ]
                num_headers = []
                for c in df.columns:
                    is_num_header = False
                    if isinstance(c, (int, float)):
                        is_num_header = True
                    else:
                        try:
                            float(str(c).replace(',', ''))
                            is_num_header = True
                        except Exception:
                            is_num_header = False
                    if is_num_header:
                        num_headers.append(c)

                # Build one or more rows from headers-as-data
                if len(str_headers) >= 1 and len(num_headers) >= 1:
                    rows = []
                    for s in str_headers:
                        # Use the first numeric header as the amount for this sheet
                        amt_header = num_headers[0]
                        try:
                            amt_val = float(str(amt_header).replace(',', ''))
                        except Exception:
                            amt_val = pd.NA
                        rows.append({
                            'GL Description': str(s).strip(),
                            adj_column_name: amt_val
                        })
                    hdr_df = pd.DataFrame(rows)
                    hdr_df[adj_column_name] = _to_numeric(hdr_df[adj_column_name])
                    print(f" Parsed adjustments from headers in {filename}: {len(hdr_df)} row(s)")
                    return hdr_df

                # Last resort: guess from body by content profile
                guessed_desc, guessed_amount = _guess_desc_amount_columns(df)
                if guessed_desc and guessed_amount:
                    tmp = df[[guessed_desc, guessed_amount]].copy()
                    tmp.columns = ['GL Description', adj_column_name]
                    tmp['GL Description'] = tmp['GL Description'].astype(str).str.strip()
                    tmp[adj_column_name] = _to_numeric(tmp[adj_column_name])
                    # Drop empty rows
                    tmp = tmp[(tmp['GL Description'] != '') & (tmp[adj_column_name].notna())]
                    # Aggregate by normalized description
                    tmp['__desc_key'] = _normalize_desc(tmp['GL Description'])
                    tmp = tmp.groupby(['__desc_key', 'GL Description'], as_index=False)[adj_column_name].sum()
                    tmp.drop(columns=['__desc_key'], inplace=True)
                    print(f" Guessed columns in {filename}: desc='{guessed_desc}', amount='{guessed_amount}'  {len(tmp)} row(s)")
                    return tmp

                print(f"  'GL Code' column not found in {filename}")
                print(f"   Available columns: {df.columns.tolist()}")
                return None
        
        # Find amount/adjustment column
        # Preferred for Lifeline audit file
        amount_col = None
        preferred_amount_names = [
            'total_adjusted_value', 'total adjusted value', 'total adjustment', 'total adjustments',
            'adjusted value', 'adjustment', 'adjustments', 'impact',
            'amount', 'value', 'debit', 'credit', 'dr', 'cr', 'net'
        ]
        # Normalize
        cols_lower = {c: str(c).lower().strip() for c in df.columns}
        for pref in preferred_amount_names:
            match = [c for c, l in cols_lower.items() if l == pref]
            if match:
                amount_col = match[0]
                break
        for col in df.columns:
            if amount_col:
                break
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['total_adjusted_value', 'total adjusted value', 'amount', 'adjustment', 'adjustments', 'impact', 'value', 'debit', 'credit', 'dr', 'cr', 'net']):
                amount_col = col
                break
        
        if amount_col is None:
            # Try to find any numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                amount_col = numeric_cols[0]
            else:
                print(f"  No amount column found in {filename}")
                return None
        
        # Optional description mapping (entity-specific synonyms)
        desc_map = _load_desc_mapping() if '_load_desc_mapping' in globals() else {}

        # Build result on GL Code or Description depending on availability
        if gl_code_col is not None:
            # GL-based adjustments: aggregate by GL Code
            result_df = df[[gl_code_col, amount_col]].copy()
            result_df.columns = ['GL Code', adj_column_name]
            result_df['GL Code'] = _normalize_gl_code(result_df['GL Code'])
            result_df[adj_column_name] = _to_numeric(result_df[adj_column_name])
            result_df = result_df.groupby('GL Code', as_index=False)[adj_column_name].sum()
            print(f" Loaded {filename}: {len(df)} rows  {len(result_df)} unique GL Codes, column '{adj_column_name}'")
        else:
            # Description-based adjustments: keep row-level data so that we
            # can support 1:1 row overlays when the adjustment sheet mirrors
            # the trial balance. Aggregation (by normalized description) will
            # be handled later at merge time when overlay is not applicable.
            result_df = df[[desc_col, amount_col]].copy()
            result_df.columns = ['GL Description', adj_column_name]
            result_df['GL Description'] = result_df['GL Description'].astype(str).str.strip()
            result_df[adj_column_name] = _to_numeric(result_df[adj_column_name])
            # Apply description mapping if provided
            if desc_map:
                key_before = _normalize_desc(result_df['GL Description'])
                mapped = key_before.map(lambda k: desc_map.get(k, None))
                mask = mapped.notna()
                if mask.any():
                    # Replace descriptions where mapping exists
                    result_df.loc[mask, 'GL Description'] = mapped[mask].astype(str).values
                    print(f" Applied description mapping to {int(mask.sum())} row(s) in {filename}")
            # Helper key retained for potential non-row-wise merges
            result_df['__desc_key'] = _normalize_desc(result_df['GL Description'])
            uniq = result_df['__desc_key'].nunique()
            print(f" Loaded {filename}: {len(df)} rows  {uniq} unique Descriptions, column '{adj_column_name}'")

        return result_df
        
    except Exception as e:
        print(f"  Error loading {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_adjustment_reconciliation(filename, adj_column_name):
    """
    Load an adjustment reconciliation file and extract GL Code and adjustment value.
    Falls back to manual adjustment file if reconciliation file doesn't exist.
    
    Args:
        filename: Name of the reconciliation file (e.g., 'enc_correct_period_reconciliation.xlsx')
        adj_column_name: Expected adjustment column name (e.g., 'Adj1_ENC')
    
    Returns:
        DataFrame with GL Code and adjustment column, or None if file not found
    """
    filepath = OUTPUT_FILES_DIR / filename
    
    # Try reconciliation file first
    if filepath.exists():
        try:
            df = pd.read_excel(filepath)
            
            # Expected columns: GL Code, Adj#_XXX
            if 'GL Code' not in df.columns:
                print(f"  'GL Code' column not found in {filename}")
                return None
            
            if adj_column_name not in df.columns:
                print(f"  '{adj_column_name}' column not found in {filename}")
                print(f"   Available columns: {df.columns.tolist()}")
                return None
            
            # Extract only GL Code and adjustment column
            result_df = df[['GL Code', adj_column_name]].copy()
            
            # Normalize GL Code and parse numeric amounts
            result_df['GL Code'] = _normalize_gl_code(result_df['GL Code'])
            result_df[adj_column_name] = _to_numeric(result_df[adj_column_name])
            
            # Group by GL Code and sum adjustments (handle duplicates from transaction detail)
            result_df = result_df.groupby('GL Code', as_index=False)[adj_column_name].sum()
            
            print(f" Loaded {filename}: {len(df)} rows  {len(result_df)} unique GL Codes, column '{adj_column_name}'")
            
            return result_df
            
        except Exception as e:
            print(f"  Error loading {filepath}: {e}")
            return None
    else:
        # Fallback to manual adjustment file
        print(f"  Reconciliation file not found: {filepath}")
        print(f"   Trying to load from manual adjustment file...")
        
        # Map reconciliation filename to manual adjustment filename
        manual_file_mapping = {
            'enc_correct_period_reconciliation.xlsx': 'enc_correct_period_adjustments.xlsx',
            'rb_audit_adjustments_reconciliation.xlsx': 'rb_audit_adjustments.xlsx',
            'rf_audit_adjustments_reconciliation.xlsx': 'rf_audit_adjustments.xlsx',
            'interco_adjustments_reconciliation.xlsx': 'interco_manual_adjustments.xlsx',
            'gt_india_audit_adjustments_reconciliation.xlsx': 'audit_adjustment_entries.xlsx',
            'reclass_entries_reconciliation.xlsx': 'reclass_entries_adjustments.xlsx'
        }
        
        manual_filename = manual_file_mapping.get(filename)
        if manual_filename:
            return load_adjustment_from_manual_file(manual_filename, adj_column_name)
        else:
            print(f"   No manual file mapping found for {filename}")
            print(f"   Filling with zeros for {adj_column_name}")
            return None


def generate_adjusted_trial_balance():
    """Main function to generate adjusted trial balance"""
    
    print("=" * 80)
    print("ADJUSTED TRIAL BALANCE GENERATOR")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Entity: {ENTITY.upper()}")
    print(f"Source Files: {SOURCE_FILES_DIR}")
    print(f"Output Files: {OUTPUT_FILES_DIR}")
    print()
    
    # Step 1: Load Trial Balance
    print(" Step 1: Loading unadjusted_trialbalance.xlsx...")
    tb_df = load_trial_balance()
    if tb_df is None:
        return False
    print()
    
    # Step 2: Discover adjustment files dynamically from manual-adjustments directory
    print(" Step 2: Discovering adjustment files (manual-adjustments)...")
    print()
    manual_dir = DATA_DIR / "input" / "manual-adjustments"
    adjustments_config = []
    if manual_dir.exists():
        for ext in ("*.xlsx", "*.xls"):
            for p in sorted(manual_dir.glob(ext)):
                base = p.name
                # Column name is the filename without extension, preserving user-provided naming
                col_name = p.stem
                adjustments_config.append({'file': base, 'column': col_name})
    if not adjustments_config:
        print("  No adjustment files found in manual-adjustments. Proceeding with zero adjustments.")
    
    # Step 3: Load and merge each adjustment
    print(" Step 3: Merging adjustments with Trial Balance...")
    print()
    
    result_df = tb_df.copy()

    # Decide whether GL Code is usable as a reliable join key.
    # We only rely on GL Code if it has a reasonable amount of
    # non-empty, distinct values; otherwise we fall back to
    # description-based matching for adjustments.
    use_gl_code = False
    if 'GL Code' in result_df.columns:
        gl_series = result_df['GL Code'].astype(str).str.strip()
        non_empty = gl_series[gl_series != '']
        unique_non_empty = non_empty.nunique()
        # Require at least 2 distinct non-empty codes and that they
        # cover a majority of rows; this avoids treating a single
        # blank/placeholder code as a real join key.
        if unique_non_empty >= 2 and len(non_empty) >= 0.5 * len(result_df):
            use_gl_code = True

    # Normalize description helper for description-based joins
    result_df['__desc_key'] = _normalize_desc(result_df['GL Description'])
    
    for idx, adj_config in enumerate(adjustments_config, 1):
        print(f"   [{idx}/{len(adjustments_config)}] Loading: {adj_config['file']}")
        
        # Load directly from manual file, using filename as the result column
        adj_df = load_adjustment_from_manual_file(adj_config['file'], adj_config['column'])
        
        if adj_df is not None:
            # Decide join key: prefer GL Code only when it is
            # actually informative on both TB and adjustment side;
            # otherwise fall back to description-based joins.
            gl_join_usable = False
            if use_gl_code and 'GL Code' in adj_df.columns:
                adj_gl = adj_df['GL Code'].astype(str).str.strip()
                adj_non_empty = adj_gl[adj_gl != '']
                # Require at least 2 distinct non-empty codes in the adjustment file
                if adj_non_empty.nunique() >= 2:
                    gl_join_usable = True

            if gl_join_usable:
                # GL-based join
                result_df = result_df.merge(adj_df, on='GL Code', how='left')
                # Unmatched reporting
                try:
                    tb_gl_set = set(result_df['GL Code'].dropna().astype(str))
                    adj_gl_set = set(adj_df['GL Code'].dropna().astype(str))
                    unmatched = len(adj_gl_set - tb_gl_set)
                    if unmatched:
                        print(f"        {adj_config['file']}: {unmatched} adjustment GL(s) not found in TB")
                except Exception:
                    pass
            elif 'GL Description' in adj_df.columns:
                adj_df = adj_df.copy()

                # Special case: row-wise overlay adjustments.
                # If the adjustment file has the same number of rows as the
                # trial balance and the normalized descriptions match in order,
                # we treat it as a 1:1 row overlay and apply the adjustment
                # amounts by row instead of description-level aggregation.
                try:
                    if len(adj_df) == len(result_df):
                        tb_keys_seq = _normalize_desc(result_df['GL Description'])
                        adj_keys_seq = _normalize_desc(adj_df['GL Description'])
                        if tb_keys_seq.reset_index(drop=True).equals(
                            adj_keys_seq.reset_index(drop=True)
                        ):
                            result_df[adj_config['column']] = adj_df[adj_config['column']].fillna(0.0).values
                            print(f"        {adj_config['file']}: applied row-wise matching on description")
                            print()
                            continue
                except Exception:
                    # If anything goes wrong, fall back to description-based merge
                    pass

                # Normalized description key for aggregation / fuzzy matching
                adj_df['__desc_key'] = _normalize_desc(adj_df['GL Description'])
                # Fuzzy map any unmatched adjustment descriptions to the closest TB description
                try:
                    import difflib
                    tb_keys = set(result_df['__desc_key'].dropna().tolist())
                    map_count = 0
                    for i in adj_df.index:
                        key = adj_df.at[i, '__desc_key']
                        if key in tb_keys or key == '':
                            continue
                        candidates = difflib.get_close_matches(key, list(tb_keys), n=1, cutoff=0.8)
                        if candidates:
                            adj_df.at[i, '__desc_key'] = candidates[0]
                            map_count += 1
                    if map_count:
                        print(f"        {adj_config['file']}: fuzz-mapped {map_count} description(s) to TB")
                except Exception:
                    pass

                # Aggregate adjustments by normalized description to avoid
                # duplicating rows when there are multiple adjustment rows
                # for the same description.
                agg_cols = [adj_config['column']]
                agg_df = adj_df.groupby('__desc_key', as_index=False)[agg_cols].sum()

                result_df = result_df.merge(agg_df, on='__desc_key', how='left')
                # Unmatched reporting for descriptions
                try:
                    tb_desc_set = set(result_df['__desc_key'].dropna())
                    adj_desc_set = set(adj_df['__desc_key'].dropna())
                    unmatched = len(adj_desc_set - tb_desc_set)
                    if unmatched:
                        print(f"        {adj_config['file']}: {unmatched} adjustment description(s) not found in TB (after normalization)")
                except Exception:
                    pass
            else:
                print(f"        {adj_config['file']}: No usable join key; creating zero-filled column")
                result_df[adj_config['column']] = 0.0
                print()
                continue
            # Fill NaN values with 0.0 for GL Codes not in adjustment file
            result_df[adj_config['column']] = result_df[adj_config['column']].fillna(0.0)
        else:
            # If file not found, create column with all zeros
            result_df[adj_config['column']] = 0.0
            print(f"        Created zero-filled column: {adj_config['column']}")
        
        print()
    
    # Step 4: Calculate final adjusted value
    # Use the same short period label chosen in load_trial_balance
    short_label = globals().get('_SHORT_PERIOD_LABEL', "Mar'25")
    print(f" Step 4: Calculating {short_label} Adjusted...")
    
    # Sum all dynamic adjustment columns
    adjustment_columns = [adj['column'] for adj in adjustments_config]
    
    # Calculate total adjustments
    result_df['Total_Adjustments'] = result_df[adjustment_columns].sum(axis=1)
    
    # Calculate final adjusted value = Original + All Adjustments
    result_df[f"{short_label} Adjusted"] = result_df[f"(Unaudited) {short_label}"] + result_df['Total_Adjustments']
    
    # Round to 2 decimal places
    result_df[f"{short_label} Adjusted"] = result_df[f"{short_label} Adjusted"].round(2)
    
    # Also round adjustment columns to 2 decimals for consistency
    for col in adjustment_columns:
        result_df[col] = result_df[col].round(2)
    
    print(f" Calculated adjusted values for {len(result_df)} GL Codes")
    print()
    
    # Step 5: Prepare final output structure
    print(" Step 5: Preparing final output structure...")
    
    # Final column order: GL Code, GL Description, (Unaudited) {period}, then one column per uploaded adjustment file
    output_columns = [
        'GL Code',
        'GL Description',
        f"(Unaudited) {short_label}",
    ] + adjustment_columns + [f"{short_label} Adjusted"]
    
    final_df = result_df[output_columns].copy()
    # Drop helper column if present
    if '__desc_key' in result_df.columns:
        result_df.drop(columns=['__desc_key'], inplace=True, errors='ignore')
    # Clean up 'nan' strings in GL Code for a nicer sheet
    if 'GL Code' in final_df.columns:
        final_df['GL Code'] = final_df['GL Code'].replace({'nan': ''})
    
    print(f" Final structure: {len(final_df)} rows x {len(output_columns)} columns")
    print()
    
    # Step 6: Display summary statistics
    print(" Step 6: Summary Statistics...")
    original_total = final_df[f"(Unaudited) {short_label}"].sum()
    adjusted_total = final_df[f"{short_label} Adjusted"].sum()
    print(f"   Original (Unaudited) {short_label}: {original_total:>15,.2f}")
    for col in adjustment_columns:
        print(f"   {col: <30} {final_df[col].sum():>15,.2f}")
    print(f"   " + "-" * 40)
    print(f"   Final {short_label} Adjusted:       {adjusted_total:>15,.2f}")
    print()
    
    # Step 7: Save output file
    print(" Step 7: Saving adjusted_trialbalance.xlsx...")
    output_path = OUTPUT_FILES_DIR / "adjusted_trialbalance.xlsx"
    
    try:
        # Delete existing file if it exists
        if output_path.exists():
            output_path.unlink()
        
        # Save to Excel
        final_df.to_excel(output_path, index=False, engine='openpyxl')
        
        file_size = output_path.stat().st_size
        print(f" File saved successfully!")
        print(f"   Location: {output_path}")
        print(f"   Size: {file_size:,} bytes")
        print(f"   Rows: {len(final_df):,}")
        print(f"   Columns: {len(output_columns)}")
        print()
        
    except Exception as e:
        print(f" Error saving file: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 8: Display preview
    print(" Preview (first 10 rows):")
    print("=" * 120)
    preview_df = final_df.head(10)
    print(preview_df.to_string(index=False))
    print("=" * 120)
    print()
    
    print(" Adjusted Trial Balance generation completed successfully!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return True


def main():
    """Entry point for the script"""
    try:
        success = generate_adjusted_trial_balance()
        return success
    except Exception as e:
        print(f" Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
def _derive_period_labels():
    """Derive period labels from global period config.

    Returns a tuple of (tb_amount_candidates, short_label) where:
    - tb_amount_candidates: list of column-name candidates to look for in the TB
    - short_label: like "Mar'25" or "Jun'25" used for final column naming
    """
    col = period_config.get_current_period_column(default="(Unaudited) Mar'25")
    normalized = col.strip()

    # Extract month/year hints
    months_full = {
        'january': 'Jan', 'february': 'Feb', 'march': 'Mar', 'april': 'Apr',
        'may': 'May', 'june': 'Jun', 'july': 'Jul', 'august': 'Aug',
        'september': 'Sep', 'october': 'Oct', 'november': 'Nov', 'december': 'Dec'
    }

    # Try to find any month and year 2-digit
    text = normalized.replace("\u2019", "'")  # right single quote  '
    month_abbr = None
    year_two = None
    for full, abbr in months_full.items():
        if full in text.lower() or abbr.lower() in text.lower():
            month_abbr = abbr
            break
    import re
    m = re.search(r"(\d{2})\b", text)
    if m:
        year_two = m.group(1)
    # Fallback for 'Mar\'25' formats
    if year_two is None:
        m2 = re.search(r"'(\d{2})", text)
        if m2:
            year_two = m2.group(1)

    if month_abbr is None:
        # fallback to Mar
        month_abbr = 'Mar'
    if year_two is None:
        year_two = '25'

    short_label = f"{month_abbr}'{year_two}"

    # Build common TB column candidates
    candidates = [
        f"(Unaudited) {short_label}",
        f"Unaudited {short_label}",
        f"Total {month_abbr} {year_two}",
        f"Total {month_abbr}'{year_two}",
        f"{month_abbr}'{year_two}",
        f"Closing {month_abbr}'{year_two}",
    ]
    return candidates, short_label
