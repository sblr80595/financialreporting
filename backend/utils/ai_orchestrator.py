"""
INTEGRIS AI ADJUSTMENT ORCHESTRATOR - ALL ADJUSTMENTS PROCESSOR
================================================================

This script processes all 6 adjustment prompts sequentially using Claude AI.
Each prompt is sent to Claude which generates and executes the appropriate code.

Usage:
    python ai_orchestrator.py [entity]
    
    entity: Entity code (default: cpm)
            Examples: cpm, hausen, integris

Each adjustment:
    - Loads configuration from data/{entity}/input/config/adjustment_config.json
    - Loads prompt from backend.config.trialbalance_preparation_prompts
    - Sends to Claude AI for code generation
    - Executes generated code
    - Saves output to data/{entity}/output/adjusted-trialbalance/
    - Validates 6 rules (if applicable)
    - Generates final adjusted trial balance
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import time
import traceback
from pathlib import Path

# Add project root to Python path BEFORE any backend imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None
# COMMENTED OUT - Gemini integration
# import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import entity configuration for proper normalization
from backend.config.entities import EntityConfig
from backend.config.period_config import period_config
# Import trial balance preparation prompts
from backend.config.trialbalance_preparation_prompts import (
    PROMPT_ENC_CORRECT_PERIOD,
    PROMPT_ROLL_BACK_AUDIT_ADJUSTMENTS,
    PROMPT_ROLL_FORWARD_AUDIT_ADJUSTMENTS,
    PROMPT_INTERCO_ADJUSTMENTS,
    PROMPT_GT_INDIA_AUDIT_ADJUSTMENTS,
    PROMPT_RECLASSIFICATION_ENTRIES_ADJUSTMENTS
)

# Get entity from environment variable or command line argument, default to 'cpm'
raw_entity = os.getenv('ENTITY', sys.argv[1] if len(sys.argv) > 1 else 'cpm')
ENTITY = EntityConfig.normalize_entity_code(raw_entity)  # Properly normalize entity code
DATA_DIR = Path(__file__).parent.parent.parent / "data" / ENTITY
SOURCE_FILES_DIR = DATA_DIR / "input" / "unadjusted-trialbalance"
MANUAL_ADJUSTMENTS_DIR = DATA_DIR / "input" / "manual-adjustments"
OUTPUT_FILES_DIR = DATA_DIR / "output" / "adjusted-trialbalance"
DEBUG_DIR = Path(__file__).parent.parent.parent / "debug"

# Ensure output directory exists
OUTPUT_FILES_DIR.mkdir(parents=True, exist_ok=True)
MANUAL_ADJUSTMENTS_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

# If caller provided period via environment, apply it here so child imports use it
PERIOD_KEY = os.getenv('PERIOD_KEY', '').strip()
PERIOD_COLUMN = os.getenv('PERIOD_COLUMN', '').strip()
try:
    if PERIOD_KEY:
        period_config.set_period(PERIOD_KEY)
    elif PERIOD_COLUMN:
        period_config.set_period_column(PERIOD_COLUMN)
except Exception:
    # Non-fatal; generator will still use its own defaults
    pass


def load_adjustment_config():
    """Load adjustment configuration from JSON file"""
    config_path = DATA_DIR / "input" / "config" / "adjustment_config.json"
    
    if not config_path.exists():
        print(f"Warning: adjustment_config.json not found at {config_path}")
        print("    Using hardcoded default configuration")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Transform config format to internal format
        adjustments = []
        for adj in config.get('adjustments', []):
            adjustments.append({
                'id': adj['id'],
                'name': adj['name'],
                'prompt_file': adj['prompt_file'],
                'data_files': adj.get('source_files', []),
                'output_file': str(OUTPUT_FILES_DIR / adj['output_file'])
            })
        
        print(f" Loaded {len(adjustments)} adjustments from config file")
        return adjustments
    except Exception as e:
        print(f"  Error loading adjustment_config.json: {str(e)}")
        print("    Using hardcoded default configuration")
        return None


def get_anthropic_client():
    """Initialize Anthropic client with API key"""
    load_dotenv()
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print(" ERROR: ANTHROPIC_API_KEY not found")
        print("Please ensure your API key is set in one of these ways:")
        print("1. Create a .env file with: ANTHROPIC_API_KEY=your-api-key-here")
        print("2. Set environment variable: export ANTHROPIC_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Ensure the library is available
    if Anthropic is None:
        print(" ERROR: 'anthropic' SDK not available. Install with: pip install anthropic")
        sys.exit(1)

    try:
        # Initialize Anthropic client with the latest SDK (v0.71.0+)
        client = Anthropic(api_key=api_key)
        print(" Anthropic client initialized successfully")
        return client
    except Exception as e:
        print(f" ERROR initializing Anthropic client: {str(e)}")
        print(f"   Make sure you have anthropic>=0.71.0 installed")
        print(f"   Run: pip install --upgrade anthropic")
        sys.exit(1)


def load_prompt_file(prompt_file):
    """Load prompt content from file or module
    
    Args:
        prompt_file: Can be either:
            - A file path (legacy support for .txt files)
            - A prompt identifier (e.g., 'PROMPT_ENC_CORRECT_PERIOD')
    
    Returns:
        tuple: (content, error) where content is the prompt string and error is None on success
    """
    # Map of prompt identifiers to actual prompt constants
    PROMPT_MAP = {
        'PROMPT_ENC_CORRECT_PERIOD': PROMPT_ENC_CORRECT_PERIOD,
        'PROMPT_ROLL_BACK_AUDIT_ADJUSTMENTS': PROMPT_ROLL_BACK_AUDIT_ADJUSTMENTS,
        'PROMPT_ROLL_FORWARD_AUDIT_ADJUSTMENTS': PROMPT_ROLL_FORWARD_AUDIT_ADJUSTMENTS,
        'PROMPT_INTERCO_ADJUSTMENTS': PROMPT_INTERCO_ADJUSTMENTS,
        'PROMPT_GT_INDIA_AUDIT_ADJUSTMENTS': PROMPT_GT_INDIA_AUDIT_ADJUSTMENTS,
        'PROMPT_RECLASSIFICATION_ENTRIES_ADJUSTMENTS': PROMPT_RECLASSIFICATION_ENTRIES_ADJUSTMENTS
    }
    
    # Check if it's a prompt identifier
    if prompt_file in PROMPT_MAP:
        return PROMPT_MAP[prompt_file], None
    
    # Legacy support: try to load from file
    if not os.path.exists(prompt_file):
        return None, f"Prompt file not found: {prompt_file}"
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return content, None
    except Exception as e:
        return None, f"Error reading prompt file: {str(e)}"


def analyze_data_files(file_list):
    """Analyze available data files and create context for Claude"""
    context = "DATA FILES AVAILABLE:\n\n"
    
    for file_name in file_list:
        # Determine which directory to look in
        # Trial Balance is in unadjusted-trialbalance, adjustment files are in manual-adjustments
        if ("Trial Balance" in file_name or 
            file_name.startswith("TB_") or 
            file_name.startswith("trial_balance") or 
            "unadjusted_trialbalance" in file_name):
            file_path = SOURCE_FILES_DIR / file_name
            file_location = "unadjusted-trialbalance"
        else:
            file_path = MANUAL_ADJUSTMENTS_DIR / file_name
            file_location = "manual-adjustments"
        
        if not file_path.exists():
            context += f" {file_name}: NOT FOUND in {file_location}/\n"
            context += f"   Expected path: {file_path}\n\n"
            continue
        
        try:
            file_size = file_path.stat().st_size
            context += f" {file_name} (from {file_location}/)\n"
            context += f"  - Path: {file_path}\n"
            context += f"  - Size: {file_size:,} bytes\n"
            
            if str(file_path).endswith('.xlsx'):
                # Special handling for files with complex headers
                if "Adjustment Entries" in file_name:
                    # Read without header first to see structure
                    df_raw = pd.read_excel(file_path, header=None, nrows=10)
                    context += f"  - IMPORTANT: This file has a complex header structure\n"
                    context += f"  - The actual header is on row 2 (index 2)\n"
                    context += f"  - Column names: {list(df_raw.iloc[2])}\n"
                    context += f"  - Use: pd.read_excel(file_path, header=2) to load correctly\n"
                    
                    # Get full row count
                    df_full = pd.read_excel(file_path, header=2)
                    context += f"  - Total rows (after header): {len(df_full):,}\n"
                    context += f"  - Sample data (first 2 rows after header):\n"
                    context += df_full.head(2).to_string(index=False)
                    context += "\n"
                else:
                    # Normal file with standard header
                    df = pd.read_excel(file_path)
                    context += f"  - Columns: {list(df.columns)}\n"
                    context += f"  - Total rows: {len(df):,}\n"
                    context += f"  - Sample data (first 2 rows):\n"
                    context += df.head(2).to_string(index=False)
                    context += "\n"
            
            context += "\n"
            
        except Exception as e:
            context += f"  - Error analyzing: {str(e)}\n\n"
    
    return context


def extract_python_code(response_text):
    """Extract Python code from Claude's markdown response"""
    text = response_text.strip()
    
    # Check if response is wrapped in ```python ... ```
    if '```python' in text:
        start_marker = '```python'
        end_marker = '```'
        
        start_idx = text.find(start_marker)
        if start_idx != -1:
            start_idx += len(start_marker)
            end_idx = text.find(end_marker, start_idx)
            
            if end_idx != -1:
                code = text[start_idx:end_idx].strip()
                return code
    
    # Check for generic code blocks ```...```
    elif text.startswith('```') and '```' in text[3:]:
        lines = text.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```') and not in_code_block:
                in_code_block = True
                continue
            elif line.strip() == '```' and in_code_block:
                break
            elif in_code_block:
                code_lines.append(line)
        
        return '\n'.join(code_lines)
    
    # If no code blocks found, return as is
    return text


def send_to_claude(client, prompt_content, data_context, output_file):
    """Send prompt to Claude AI for code generation"""
    
    system_message = f"""You are an expert Python developer specializing in financial data processing and audit adjustments.

Your task is to generate CLEAN, EXECUTABLE Python code based on the requirements provided.

CRITICAL REQUIREMENTS:
1. Import pandas as 'pd' at the top
2. Load Trial Balance from: '{SOURCE_FILES_DIR}'
3. Load adjustment files from: '{MANUAL_ADJUSTMENTS_DIR}'
4. Save output to the exact file path specified
5. Include proper error handling
6. Print progress messages during execution
7. Follow the exact logic specified in the prompt

IMPORTANT: Return ONLY executable Python code. Do NOT include:
- Markdown formatting or code blocks
- Explanations or comments outside the code
- Any text before or after the code

The code will be executed directly using exec()."""

    user_message = f"""Generate Python code to process this financial adjustment:

===== REQUIREMENTS =====
{prompt_content}

===== DATA AVAILABLE =====
{data_context}

===== DIRECTORY STRUCTURE =====
- Trial Balance files: {SOURCE_FILES_DIR}/
- Adjustment files: {MANUAL_ADJUSTMENTS_DIR}/
- Output directory: {Path(output_file).parent}/

===== OUTPUT FILE =====
{output_file}

Generate complete, executable Python code that:
1. Loads Trial Balance from {SOURCE_FILES_DIR}/
2. Loads adjustment files from {MANUAL_ADJUSTMENTS_DIR}/
3. Processes the data according to all requirements above
3. Saves the reconciliation report to: {output_file}
4. Prints progress and summary statistics

Return ONLY the Python code, no markdown, no explanations."""

    try:
        # Get model from environment
        model = os.getenv('ANTHROPIC_MODEL', 'claude-haiku-4-5-20251001')
        max_tokens = int(os.getenv('LLM_MAX_TOKENS', '8000'))
        
        print(f"\n Calling Claude API...")
        print(f"   Model: {model}")
        print(f"   Max tokens: {max_tokens}")
        print(f"   Prompt length: {len(prompt_content)} characters")
        print(f"   Data context: {len(data_context)} characters")
        print(f"    Please wait... (typically 30-60 seconds)")
        
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_message,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        code_response = response.content[0].text
        print(f" Received response from Claude ({len(code_response)} characters)")
        
        # Show preview of what Claude returned
        preview = code_response[:150].replace('\n', ' ')
        print(f" Response preview: {preview}...")
        
        return code_response, None
        
    except Exception as e:
        error_msg = f"Claude API error: {type(e).__name__}: {str(e)}"
        print(f" {error_msg}")
        
        # Provide helpful debugging information
        if "api_key" in str(e).lower():
            print(" TIP: Check that ANTHROPIC_API_KEY is set in your .env file")
        elif "rate_limit" in str(e).lower():
            print(" TIP: Rate limit exceeded. Please wait a moment and try again")
        elif "timeout" in str(e).lower():
            print(" TIP: Request timed out. Check your internet connection")
        
        traceback.print_exc()
        return None, error_msg

def execute_generated_code(code_response, adjustment_name):
    """Execute Claude-generated code with detailed logging"""
    
    print("\n  Processing Claude's response...")
    
    # Extract Python code from markdown
    clean_code = extract_python_code(code_response)
    
    # Show code preview
    code_lines = clean_code.split('\n')
    print(f" Generated code: {len(code_lines)} lines")
    print(f"   Preview (first 5 lines):")
    for i, line in enumerate(code_lines[:5], 1):
        print(f"   {i:2d}: {line}")
    if len(code_lines) > 5:
        print(f"   ... ({len(code_lines) - 5} more lines)")
    
    # Validate syntax
    print("\n Validating code syntax...")
    try:
        compile(clean_code, '<string>', 'exec')
        print(" Syntax validation passed")
    except SyntaxError as se:
        print(f" Syntax Error at line {se.lineno}:")
        print(f"   {se.text}")
        if se.offset:
            print(f"   {' ' * (se.offset - 1)}^")
        print(f"   Error: {se.msg}")
        
        # Save for debugging
        debug_file = DEBUG_DIR / "debug_syntax_error.py"
        with open(debug_file, 'w') as f:
            f.write("# SYNTAX ERROR DETECTED\n")
            f.write(f"# Error: {se.msg} at line {se.lineno}\n\n")
            f.write(clean_code)
        print(f" Code saved to: {debug_file}")
        
        return False, f"Syntax error at line {se.lineno}: {se.msg}"
    
    # Execute the code
    print("\n Executing generated code...")
    print("=" * 60)
    
    try:
        # Create execution environment
        exec_globals = {
            '__builtins__': __builtins__,
            'pd': pd,
            'os': os,
            'json': json,
            'datetime': datetime
        }
        
        # Execute
        exec(clean_code, exec_globals)
        
        print("=" * 60)
        print(" Code execution completed successfully")
        return True, None
        
    except Exception as e:
        print("=" * 60)
        error_msg = f"Runtime error: {type(e).__name__}: {str(e)}"
        print(f" {error_msg}")
        print("\n Full traceback:")
        traceback.print_exc()
        
        # Save for debugging
        debug_file = DEBUG_DIR / "debug_runtime_error.py"
        with open(debug_file, 'w') as f:
            f.write(f"# RUNTIME ERROR\n")
            f.write(f"# Error: {type(e).__name__}: {str(e)}\n\n")
            f.write(clean_code)
        print(f"\n Code saved to: {debug_file}")
        
        return False, error_msg


def _gt_india_fallback_process(adjustment_config, output_file):
    """Deterministic fallback processor for GT India audit adjustments.

    This function performs a robust read/normalize/filter/aggregate/save flow
    that avoids boolean Series alignment issues by always creating Series with
    the same index as the DataFrame.
    Returns: (success: bool, error: Optional[str])
    """
    try:
        print("  Running GT India fallback processor...")
        # Load trial balance
        tb_path = SOURCE_FILES_DIR / 'unadjusted_trialbalance.xlsx'
        if not tb_path.exists():
            return False, f"Trial balance not found: {tb_path}"

        tb_df = pd.read_excel(tb_path)

        # Determine audit adjustment filename from config
        data_files = adjustment_config.get('data_files', [])
        audit_file = None
        if len(data_files) >= 2:
            audit_file = data_files[1]
        if not audit_file:
            audit_file = 'audit_adjustment_entries.xlsx'

        audit_path = MANUAL_ADJUSTMENTS_DIR / audit_file
        if not audit_path.exists():
            return False, f"Audit adjustments file not found: {audit_path}"

        audit_df = pd.read_excel(audit_path)

        # Normalization helper
        def normalize_gl_code(code):
            """Normalize GL codes by converting to string and lowercasing for comparison"""
            if pd.isna(code):
                return None
            try:
                # Convert to string, strip whitespace, and convert to lowercase
                code_str = str(code).strip().strip("'").lower()
                if not code_str or code_str == 'nan':
                    return None
                return code_str
            except Exception:
                return None

        tb_df['GL_Code_Normalized'] = tb_df.get('GL Code', tb_df.columns[0]).apply(normalize_gl_code) if 'GL Code' in tb_df.columns else tb_df.iloc[:,0].apply(normalize_gl_code)
        tb_df = tb_df[tb_df['GL_Code_Normalized'].notna()].copy()

        audit_df['GL_Code_Normalized'] = audit_df.get('GL Code', audit_df.columns[0]).apply(normalize_gl_code) if 'GL Code' in audit_df.columns else audit_df.iloc[:,0].apply(normalize_gl_code)
        audit_df = audit_df[audit_df['GL_Code_Normalized'].notna()].copy()

        # Safely get journal and remarks columns by position if present; always align index
        journal_col = pd.Series([''] * len(audit_df), index=audit_df.index)
        remarks_col = pd.Series([''] * len(audit_df), index=audit_df.index)

        if audit_df.shape[1] > 9:
            journal_col = audit_df.iloc[:, 9].fillna('').astype(str).reindex(audit_df.index)
        if audit_df.shape[1] > 12:
            remarks_col = audit_df.iloc[:, 12].fillna('').astype(str).reindex(audit_df.index)

        mask = ~((journal_col.str.contains('to be deleted', case=False, na=False)) |
                 (remarks_col.str.contains('to be deleted', case=False, na=False)))

        # Apply mask safely
        audit_df = audit_df.loc[mask]

        # Determine adjustment value column
        if 'total_adjusted_value' in audit_df.columns:
            value_col = 'total_adjusted_value'
        else:
            # Try to infer numeric columns that contain 'GT Audit Adj' or are numeric
            candidates = [c for c in audit_df.columns if 'gt audit adj' in str(c).lower()]
            if candidates:
                # Sum candidate columns into a total
                audit_df['total_adjusted_value'] = audit_df[candidates].select_dtypes(include='number').sum(axis=1)
                value_col = 'total_adjusted_value'
            else:
                # Fallback: use any numeric column besides GL code
                numeric_cols = audit_df.select_dtypes(include='number').columns.tolist()
                numeric_cols = [c for c in numeric_cols if c != 'GL_Code_Normalized']
                if numeric_cols:
                    audit_df['total_adjusted_value'] = audit_df[numeric_cols].sum(axis=1)
                    value_col = 'total_adjusted_value'
                else:
                    return False, 'No numeric adjustment column found in audit adjustments file.'

        # Aggregate
        audit_grouped = audit_df.groupby('GL_Code_Normalized')[value_col].sum().reset_index()
        audit_grouped.columns = ['GL_Code_Normalized', 'Total_Adjustment']

        # Build reconciliation
        results = []
        # Try to find the Mar'25 column (various naming possibilities)
        mar25_candidates = [c for c in tb_df.columns if "mar'25" in str(c).lower() or "mar25" in str(c).lower() or "mar 25" in str(c).lower()]
        mar_col = mar25_candidates[0] if mar25_candidates else tb_df.columns[-1]

        for _, tb_row in tb_df.iterrows():
            gl_code = tb_row['GL_Code_Normalized']
            gl_description = tb_row.get('GL Description', '') if 'GL Description' in tb_row.index else ''
            original_mar25 = tb_row.get(mar_col, 0)

            adj_match = audit_grouped[audit_grouped['GL_Code_Normalized'] == gl_code]
            total_adjustment = float(adj_match['Total_Adjustment'].iloc[0]) if not adj_match.empty else 0.0

            adjusted_mar25 = (original_mar25 if pd.notna(original_mar25) else 0.0) + total_adjustment

            results.append({
                'GL Code': gl_code,  # Use normalized string format for GL codes
                'GL Description': gl_description,
                "Original Mar'25": original_mar25,
                'Total Adjustment': total_adjustment,
                "Adjusted Mar'25": adjusted_mar25
            })

        reconciliation_df = pd.DataFrame(results)
        if reconciliation_df.empty:
            return False, 'Reconciliation resulted in empty DataFrame.'

        # Keep GL Code as string (already normalized to lowercase) for proper matching
        reconciliation_df['GL Code'] = reconciliation_df['GL Code'].astype(str).str.lower()
        reconciliation_df = reconciliation_df.sort_values('GL Code').reset_index(drop=True)

        # Summary
        total_original = reconciliation_df["Original Mar'25"].sum()
        total_adjustments = reconciliation_df['Total Adjustment'].sum()
        total_adjusted = reconciliation_df["Adjusted Mar'25"].sum()

        summary_data = {
            'Metric': [
                'Total GL Codes Processed',
                'GL Codes with Adjustments',
                'GL Codes without Adjustments',
                'Total Original Mar\'25',
                'Total Audit Adjustments',
                'Total Adjusted Mar\'25',
                'Reconciliation Status'
            ],
            'Value': [
                len(reconciliation_df),
                (reconciliation_df['Total Adjustment'] != 0).sum(),
                (reconciliation_df['Total Adjustment'] == 0).sum(),
                f"{total_original:,.2f}",
                f"{total_adjustments:,.2f}",
                f"{total_adjusted:,.2f}",
                'PASS' if abs(total_adjusted - (total_original + total_adjustments)) < 0.01 else 'FAIL'
            ]
        }

        summary_df = pd.DataFrame(summary_data)

        # Ensure output folder exists
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        # Save
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            reconciliation_df.to_excel(writer, sheet_name='Reconciliation', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

        return True, None

    except Exception as e:
        import traceback as _tb
        _tb.print_exc()
        return False, f"Fallback processing error: {type(e).__name__}: {str(e)}"


def process_single_adjustment(client, adjustment_config):
    """Process a single adjustment"""
    
    prompt_file = adjustment_config['prompt_file']
    data_files = adjustment_config['data_files']
    output_file = adjustment_config['output_file']
    adjustment_name = adjustment_config['name']
    
    print(f"\n{'='*80}")
    print(f"PROCESSING ADJUSTMENT #{adjustment_config['id']}: {adjustment_name}")
    print(f"{'='*80}")
    print(f"  Started at: {datetime.now().strftime('%H:%M:%S')}")
    print(f" Prompt: {prompt_file}")
    print(f" Output: {output_file}")
    print(f"{'='*80}")
    
    # Load prompt
    print(f"\n Step 1/4: Loading prompt template...")
    prompt_content, error = load_prompt_file(prompt_file)
    if error:
        print(f" ERROR: Failed to load prompt - {error}")
        return False, error
    print(f" Prompt loaded successfully ({len(prompt_content)} characters)")
    
    # Analyze data files
    print(f"\n Step 2/4: Analyzing input data files...")
    data_context = analyze_data_files(data_files)
    print(data_context)
    
    # Send to Claude
    print(f"\n Step 3/4: Sending to Claude AI for code generation...")
    print(f"   (This may take 30-60 seconds depending on complexity)")
    code_response, error = send_to_claude(client, prompt_content, data_context, output_file)
    if error:
        print(f" ERROR: Claude API failed - {error}")
        return False, error
    print(f" Received code from Claude AI ({len(code_response)} characters)")
    
    # Execute generated code
    print(f"\n Step 4/4: Executing generated code...")
    success, error = execute_generated_code(code_response, adjustment_name)
    
    # Check output file
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"\n SUCCESS: Output file created")
        print(f"    File: {output_file}")
        print(f"    Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    else:
        print(f"\n  WARNING: Output file not found at: {output_file}")
        # If the LLM-generated code failed to write the file, attempt a safe, deterministic
        # fallback for the GT India audit adjustments (id 5). This fixes common issues
        # such as boolean Series alignment when filtering by columns that may or may not exist.
        if adjustment_config.get('id') == 5 or 'gt_india' in str(output_file).lower():
            print(" Attempting fallback processor for GT India audit adjustments...")
            try:
                fb_success, fb_error = _gt_india_fallback_process(adjustment_config, output_file)
                if fb_success and os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    print(f"\n FALLBACK SUCCESS: Output file created")
                    print(f"    File: {output_file}")
                    print(f"    Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                    success = True
                    error = None
                else:
                    print(f"\n FALLBACK FAILED: {fb_error}")
                    success = False
                    error = fb_error or "Output file not created"
            except Exception as e:
                print(f"\n Exception in fallback processor: {e}")
                import traceback as _tb
                _tb.print_exc()
                success = False
                error = str(e)
        else:
            success = False
            error = "Output file not created"
    
    print(f"\n  Completed at: {datetime.now().strftime('%H:%M:%S')}")
    
    return success, error


def main():
    """Main function to process all adjustments"""
    
    # Try to load configuration from JSON file
    ADJUSTMENTS = load_adjustment_config()
    
    # Fallback to hardcoded configuration if config file not found
    if ADJUSTMENTS is None:
        ADJUSTMENTS = [
            {
                "id": 1,
                "name": "Entries not considered in the correct period",
                "prompt_file": "PROMPT_ENC_CORRECT_PERIOD",
                "data_files": ["unadjusted_trialbalance.xlsx", "enc_correct_period_adjustments.xlsx"],
                "output_file": str(OUTPUT_FILES_DIR / "enc_correct_period_reconciliation.xlsx")
            },
            {
                "id": 2,
                "name": "Roll back of audit adjustments entries",
                "prompt_file": "PROMPT_ROLL_BACK_AUDIT_ADJUSTMENTS",
                "data_files": ["unadjusted_trialbalance.xlsx", "rb_audit_adjustments.xlsx"],
                "output_file": str(OUTPUT_FILES_DIR / "rb_audit_adjustments_reconciliation.xlsx")
            },
            {
                "id": 3,
                "name": "Roll forward entries",
                "prompt_file": "PROMPT_ROLL_FORWARD_AUDIT_ADJUSTMENTS",
                "data_files": ["unadjusted_trialbalance.xlsx", "rf_audit_adjustments.xlsx"],
                "output_file": str(OUTPUT_FILES_DIR / "rf_audit_adjustments_reconciliation.xlsx")
            },
            {
                "id": 4,
                "name": "Interco adjustments",
                "prompt_file": "PROMPT_INTERCO_ADJUSTMENTS",
                "data_files": ["unadjusted_trialbalance.xlsx", "interco_manual_adjustments.xlsx"],
                "output_file": str(OUTPUT_FILES_DIR / "interco_adjustments_reconciliation.xlsx")
            },
            {
                "id": 5,
                "name": "Audit adjustment entries proposed by GT India",
                "prompt_file": "PROMPT_GT_INDIA_AUDIT_ADJUSTMENTS",
                "data_files": ["unadjusted_trialbalance.xlsx", "audit_adjustment_entries.xlsx"],
                "output_file": str(OUTPUT_FILES_DIR / "gt_india_audit_adjustments_reconciliation.xlsx")
            },
            {
                "id": 6,
                "name": "Reclassification entries proposed by GT India",
                "prompt_file": "PROMPT_RECLASSIFICATION_ENTRIES_ADJUSTMENTS",
                "data_files": ["unadjusted_trialbalance.xlsx", "reclass_entries_adjustments.xlsx"],
                "output_file": str(OUTPUT_FILES_DIR / "reclass_entries_reconciliation.xlsx")
            }
        ]
    
    # Print header
    start_time = datetime.now()
    print("=" * 80)
    print("INTEGRIS TRIAL BALANCE ADJUSTMENT PROCESSOR")
    print("=" * 80)
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Entity: {ENTITY.upper()}")
    print(f"Trial Balance Dir: {SOURCE_FILES_DIR}")
    print(f"Manual Adjustments Dir: {MANUAL_ADJUSTMENTS_DIR}")
    print(f"Output Files Dir: {OUTPUT_FILES_DIR}")
    print()
    print("NOTE: Individual reconciliation files are no longer generated.")
    print("      Generating final adjusted trial balance directly from manual adjustments...")
    print("=" * 80)
    
    # Skip individual AI adjustments and reconciliation files
    # Go directly to consolidated trial balance generation
    
    # Track as "success" for all adjustments (no individual processing)
    results = []
    for adjustment in ADJUSTMENTS:
        result = {
            'id': adjustment['id'],
            'name': adjustment['name'],
            'status': 'SKIPPED',
            'error': None,
            'execution_time': 0,
            'output_file': adjustment['output_file']
        }
        results.append(result)
    
    # Final summary
    end_time = datetime.now()
    total_execution_time = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Total adjustments: {len(ADJUSTMENTS)}")
    print(f"Individual reconciliation files: SKIPPED (not needed)")
    print(f"Processing time: {total_execution_time:.2f} seconds")
    print()
    
    # Detailed results table
    print("ADJUSTMENTS TO BE APPLIED:")
    print("-" * 80)
    for result in results:
        print(f"   #{result['id']}: {result['name']}")
    
    print("=" * 80)
    
    # Save results to JSON (overwrite mode)
    results_file = OUTPUT_FILES_DIR / "ai_adjustment_summary.json"
    if results_file.exists():
        results_file.unlink()
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'entity': ENTITY,
            'total_execution_time': total_execution_time,
            'adjustments': results
        }, f, indent=2)
    print(f"\nResults saved to: {results_file}")
    
    # Generate the adjusted trial balance directly from manual adjustment files
    all_success = True
    
    print("\n" + "=" * 80)
    print("GENERATING ADJUSTED TRIAL BALANCE")
    print("=" * 80)
    print("Reading adjustments directly from manual adjustment files...")
    print()
    
    try:
        # Set entity environment variable for the consolidation script
        os.environ['ENTITY'] = ENTITY
        
        # Import from backend.utils directory
        from backend.utils import generate_consolidate_tb
        tb_success = generate_consolidate_tb.main()
        
        if tb_success:
            print("\n Adjusted Trial Balance created successfully!")
            print(f" File: {OUTPUT_FILES_DIR / 'adjusted_trialbalance.xlsx'}")
        else:
            print("\n  Failed to generate Adjusted Trial Balance")
            print(f"   You can manually run: python utils/generate_consolidate_tb.py {ENTITY}")
            all_success = False
            
    except Exception as e:
        print(f"\n  Error generating Adjusted Trial Balance: {e}")
        import traceback
        traceback.print_exc()
        print(f"   You can manually run: python utils/generate_consolidate_tb.py {ENTITY}")
        all_success = False
    
    return all_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
