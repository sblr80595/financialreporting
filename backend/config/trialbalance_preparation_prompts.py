"""
Trial Balance Preparation Prompts
==================================

This module contains all the prompts used for trial balance preparation
and adjustment processing via AI orchestration.
"""

# Prompt for Adjustment #1 - Entries Not Considered in the Correct Period
PROMPT_ENC_CORRECT_PERIOD = """Prompt for Adjustment #1 – Entries Not Considered in the Correct Period

BUSINESS CONTEXT
This adjustment ensures compliance with accrual accounting principles by correctly reflecting transactions in their respective reporting periods. Certain entries were initially recorded outside the appropriate timeframe, which can distort financial performance and position. By reconciling these entries, we maintain accuracy, transparency, and audit readiness in the financial statements, supporting reliable decision-making and regulatory compliance.

OBJECTIVE
Process Adjustment #1 by reconciling entries that were not recorded in the correct accounting period. The goal is to:
	•	Match GL Codes between the source trial balance and the adjustment file.
	•	Generate:
	◦	A clean output file with adjustment amounts for each GL Code.
	◦	An issue report file highlighting any anomalies or data quality problems.

INPUT FILES
	1	unadjusted_trialbalance.xlsx 
	◦	Location: unadjusted-trialbalance directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"(Unaudited) Mar'25"
	2	enc_correct_period_adjustments.xlsx 
	◦	Location: manual-adjustments directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"Adj: Jan.22-Mar.22"
	▪	"Adj: Jan.23-Mar.23"
	▪	"Adj: Jan.24-Mar.24"
	▪	"total_adjusted_value"

COLUMN NAME ALIASES
	•	"GL Description" and "GL Code Description" are the same field and should be treated as interchangeable
	•	When searching for description columns, check for both variations
	•	Normalize column names during data loading to handle variations

PROCESSING RULES 
Step 1: Data Validation & Cleaning
	•	Remove empty rows and columns.
	•	Detect and ignore extra header rows (check if GL Code column contains non-numeric or repeated header text).
	•	Drop summary or total rows (detect keywords like "Total", "Summary").
	•	Normalize:
	◦	Trim whitespace in GL Codes.
	◦	**CRITICAL**: Convert ALL GL Codes to strings using str(), then convert to lowercase using .lower() for comparison.
	◦	This ensures GL codes like "34010000L" match with "34010000l" and numeric codes like 21035438 match with "21035438".
	◦	Convert numeric columns to float (handle strings, remove junk characters like commas or currency symbols).
	•	Round excessive decimal places (e.g., to 2 or 4 decimals).
	•	Flag:
	◦	Missing GL Codes.
	◦	Invalid numeric formats.
	◦	Unrecognizable characters or corrupted cells.
Step 2: Matching Logic
	•	**CRITICAL GL Code Matching Requirements**:
	◦	Convert ALL GL Codes to strings: str(gl_code).strip().lower()
	◦	This must be done for BOTH trial balance and adjustment file GL codes
	◦	Create lookup dictionaries using lowercase string GL codes as keys
	◦	Example: enc_dict[str(gl_code).strip().lower()] = value
	•	For each GL Code in unadjusted_trialbalance.xlsx:
	◦	Normalize to lowercase string: gl_key = str(gl_code).strip().lower()
	◦	Match with normalized GL Code in enc_correct_period_adjustments.xlsx using: gl_key in enc_dict
	◦	If match found: use "total_adjusted_value".
	◦	If no match: assign 0.0.
Step 3: Output Files
	•	Main Output File:
	◦	Name: enc_correct_period_reconciliation.xlsx
	◦	Columns:
	◦	"GL Code"
	◦	"Adj1_ENC"
	◦	Include all GL Codes from trial balance (no missing rows).
	•	Issue Report File:
	◦	Name: enc_correct_period_issues.xlsx
	◦	Columns:
	◦	"Row Number"
	◦	"Issue Type" (e.g., Missing GL Code, Invalid Numeric Format)
	◦	"Details"

OUTPUT REQUIREMENTS
	•	Adjustment values must be numeric (float).
	•	No extra columns or descriptions in the main output.
	•	Ensure file paths match output_file variable.

PYTHON IMPLEMENTATION REQUIREMENTS
	•	Use pandas for data processing.
	•	Reference file paths from SOURCE_FILES_DIR and MANUAL_ADJUSTMENTS_DIR.
	•	Implement:
	◦	Data cleaning.
	◦	Issue logging.
	◦	Matching logic.
	•	Print progress messages for transparency.
	•	Stop processing if critical columns (GL Code, total_adjusted_value) are missing.
	•	For removing empty columns, use: df = df.dropna(axis=1, how='all')
	•	For trimming column names, use: df.columns = df.columns.str.strip()
	•	Avoid using .eq() method on Index objects - use comparison operators instead

CRITICAL CONSTRAINTS
	•	Output must contain exactly all GL Codes from trial balance.
	•	**GL Code Matching**: MUST convert both sides to lowercase strings before comparison: str(code).strip().lower()
	•	This is CRITICAL - without lowercase conversion, codes like "34010000L" will not match "34010000l"
	•	Generate issue file for any anomalies.

EXAMPLE OUTPUT STRUCTURE
Main Output File:
GL Code     | Adj1_ENC
84036000    | 0.0
14010080    | 1250.0
14050067    | 0.0

Issue Report File:
Row Number  | Issue Type            | Details
15          | Missing GL Code       | GL Code not found in source
42          | Invalid Numeric Data  | Value: "ABC" in adjustment

QUALITY ASSURANCE CHECKLIST
Before finalizing:
	1	File Integrity – Both input files load without errors.
	2	Data Cleaning Applied – Empty rows removed, headers normalized.
	3	Issue File Generated – All anomalies logged.
	4	GL Code Coverage – Output includes all trial balance GL Codes.
	5	Numeric Conversion Verified – No strings left in numeric columns.
	6	Output Structure – Only "GL Code" and "Adj1_ENC" in main file.
	7	File Naming & Location – Matches specified paths.
	8	Progress Logging – Console confirms each major step.
"""


# Prompt for Adjustment #2 - Roll Back of Audit Adjustments Entries
PROMPT_ROLL_BACK_AUDIT_ADJUSTMENTS = """Prompt for Adjustment #2 – Roll Back of Audit Adjustments Entries

BUSINESS CONTEXT
This adjustment reverses prior audit adjustments that were applied to previous periods but are no longer valid. Rolling back these entries ensures that the trial balance reflects accurate figures for the current reporting period. This process supports financial integrity, audit compliance, and transparency, preventing misstatements in the financial statements.

OBJECTIVE
Process Adjustment #2 by:
	•	Matching GL Codes between the source trial balance and the rollback adjustment file.
	•	Generating:
	◦	A clean output file with rollback adjustment amounts for each GL Code.
	◦	An issue report file highlighting anomalies or data quality problems.

INPUT FILES
	1	unadjusted_trialbalance.xlsx 
	◦	Location: unadjusted-trialbalance directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"(Unaudited) Mar'25"
	2	rb_audit_adjustments.xlsx 
	◦	Location: manual-adjustments directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"Rollback: Apr-Dec'24"
	▪	"total_adjusted_value"

COLUMN NAME ALIASES
	•	"GL Description" and "GL Code Description" are the same field and should be treated as interchangeable
	•	When searching for description columns, check for both variations
	•	Normalize column names during data loading to handle variations

PROCESSING RULES
Step 1: Data Validation & Cleaning
	•	Remove empty rows and columns.
	•	Detect and ignore extra header rows (check if GL Code column contains non-numeric or repeated header text).
	•	Drop summary or total rows (detect keywords like "Total", "Summary").
	•	Normalize:
	◦	Trim whitespace in GL Codes.
	◦	**CRITICAL**: Convert ALL GL Codes to strings using str(), then convert to lowercase using .lower() for comparison.
	◦	This ensures GL codes like "34010000L" match with "34010000l" and numeric codes like 21035438 match with "21035438".
	◦	Convert numeric columns to float (handle strings, remove junk characters like commas or currency symbols).
	•	Round excessive decimal places (e.g., to 2 or 4 decimals).
	•	Flag:
	◦	Missing GL Codes.
	◦	Invalid numeric formats.
	◦	Unrecognizable characters or corrupted cells.
Step 2: Matching Logic
	•	**CRITICAL GL Code Matching Requirements**:
	◦	Convert ALL GL Codes to strings: str(gl_code).strip().lower()
	◦	This must be done for BOTH trial balance and adjustment file GL codes
	◦	Create lookup dictionaries using lowercase string GL codes as keys
	◦	Example: rb_dict[str(gl_code).strip().lower()] = value
	•	For each GL Code in unadjusted_trialbalance.xlsx:
	◦	Normalize to lowercase string: gl_key = str(gl_code).strip().lower()
	◦	Match with normalized GL Code in rb_audit_adjustments.xlsx using: gl_key in rb_dict
	◦	If match found: use "total_adjusted_value".
	◦	If no match: assign 0.0.
Step 3: Output Files
	•	Main Output File:
	◦	Name: rb_audit_adjustments_reconciliation.xlsx
	◦	Columns:
	◦	"GL Code"
	◦	"Adj2_RB"
	◦	Include all GL Codes from trial balance (no missing rows).
	•	Issue Report File:
	◦	Name: rb_audit_adjustments_issues.xlsx
	◦	Columns:
	◦	"Row Number"
	◦	"Issue Type" (e.g., Missing GL Code, Invalid Numeric Format)
	◦	"Details"

OUTPUT REQUIREMENTS
	•	Adjustment values must be numeric (float).
	•	No extra columns or descriptions in the main output.
	•	Ensure file paths match output_file variable.

PYTHON IMPLEMENTATION REQUIREMENTS
	•	Use pandas for data processing.
	•	Reference file paths from SOURCE_FILES_DIR and MANUAL_ADJUSTMENTS_DIR.
	•	Implement:
	◦	Data cleaning.
	◦	Issue logging.
	◦	Matching logic.
	•	Print progress messages for transparency.
	•	Stop processing if critical columns (GL Code, total_adjusted_value) are missing.
	•	For removing empty columns, use: df = df.dropna(axis=1, how='all')
	•	For trimming column names, use: df.columns = df.columns.str.strip()
	•	Avoid using .eq() method on Index objects - use comparison operators instead

CRITICAL CONSTRAINTS
	•	Output must contain exactly all GL Codes from trial balance.
	•	**GL Code Matching**: MUST convert both sides to lowercase strings before comparison: str(code).strip().lower()
	•	This is CRITICAL - without lowercase conversion, codes like "34010000L" will not match "34010000l"
	•	Generate issue file for any anomalies.

EXAMPLE OUTPUT STRUCTURE
Main Output File:
GL Code     | Adj2_RB
84036000    | 0.0
14010080    | -500.0
14050067    | 0.0

Issue Report File:
Row Number  | Issue Type            | Details
12          | Missing GL Code       | GL Code not found in source
38          | Invalid Numeric Data  | Value: "XYZ" in adjustment

QUALITY ASSURANCE CHECKLIST
Before finalizing:
	1	File Integrity – Both input files load without errors.
	2	Data Cleaning Applied – Empty rows removed, headers normalized.
	3	Issue File Generated – All anomalies logged.
	4	GL Code Coverage – Output includes all trial balance GL Codes.
	5	Numeric Conversion Verified – No strings left in numeric columns.
	6	Output Structure – Only "GL Code" and "Adj2_RB" in main file.
	7	File Naming & Location – Matches specified paths.
	8	Progress Logging – Console confirms each major step.
"""


# Prompt for Adjustment #3 - Roll Forward Entries
PROMPT_ROLL_FORWARD_AUDIT_ADJUSTMENTS = """Prompt for Adjustment #3 – Roll Forward Entries

BUSINESS CONTEXT
This adjustment applies roll-forward entries to carry forward balances from prior periods into the current reporting period. It ensures that the trial balance reflects accurate and complete figures for the current quarter, supporting financial continuity, compliance, and audit readiness.

OBJECTIVE
Process Adjustment #3 by:
	•	Matching GL Codes between the source trial balance and the roll-forward adjustment file.
	•	Generating:
	◦	A clean output file with roll-forward adjustment amounts for each GL Code.
	◦	An issue report file highlighting anomalies or data quality problems.

INPUT FILES
	1	unadjusted_trialbalance.xlsx 
	◦	Location: unadjusted-trialbalance directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"(Unaudited) Mar'25"
	2	rf_audit_adjustments.xlsx 
	◦	Location: manual-adjustments directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"Roll Forward: Jan.25-Mar.25"
	▪	"total_adjusted_value"

COLUMN NAME ALIASES
	•	"GL Description" and "GL Code Description" are the same field and should be treated as interchangeable
	•	When searching for description columns, check for both variations
	•	Normalize column names during data loading to handle variations

PROCESSING RULES
Step 1: Data Validation & Cleaning
	•	Remove empty rows and columns.
	•	Detect and ignore extra header rows (check if GL Code column contains non-numeric or repeated header text).
	•	Drop summary or total rows (detect keywords like "Total", "Summary").
	•	Normalize:
	◦	Trim whitespace in GL Codes.
	◦	**CRITICAL**: Convert ALL GL Codes to strings using str(), then convert to lowercase using .lower() for comparison.
	◦	This ensures GL codes like "34010000L" match with "34010000l" and numeric codes like 21035438 match with "21035438".
	◦	Convert numeric columns to float (handle strings, remove junk characters like commas or currency symbols).
	•	Round excessive decimal places (e.g., to 2 or 4 decimals).
	•	Flag:
	◦	Missing GL Codes.
	◦	Invalid numeric formats.
	◦	Unrecognizable characters or corrupted cells.
Step 2: Matching Logic
	•	**CRITICAL GL Code Matching Requirements**:
	◦	Convert ALL GL Codes to strings: str(gl_code).strip().lower()
	◦	This must be done for BOTH trial balance and adjustment file GL codes
	◦	Create lookup dictionaries using lowercase string GL codes as keys
	◦	Example: rf_dict[str(gl_code).strip().lower()] = value
	•	For each GL Code in unadjusted_trialbalance.xlsx:
	◦	Normalize to lowercase string: gl_key = str(gl_code).strip().lower()
	◦	Match with normalized GL Code in rf_audit_adjustments.xlsx using: gl_key in rf_dict
	◦	If match found: use "total_adjusted_value".
	◦	If no match: assign 0.0.
Step 3: Output Files
	•	Main Output File:
	◦	Name: rf_audit_adjustments_reconciliation.xlsx
	◦	Columns:
	◦	"GL Code"
	◦	"Adj3_RF"
	◦	Include all GL Codes from trial balance (no missing rows).
	•	Issue Report File:
	◦	Name: rf_audit_adjustments_issues.xlsx
	◦	Columns:
	◦	"Row Number"
	◦	"Issue Type" (e.g., Missing GL Code, Invalid Numeric Format)
	◦	"Details"

OUTPUT REQUIREMENTS
	•	Adjustment values must be numeric (float).
	•	No extra columns or descriptions in the main output.
	•	Ensure file paths match output_file variable.

PYTHON IMPLEMENTATION REQUIREMENTS
	•	Use pandas for data processing.
	•	Reference file paths from SOURCE_FILES_DIR and MANUAL_ADJUSTMENTS_DIR.
	•	Implement:
	◦	Data cleaning.
	◦	Issue logging.
	◦	Matching logic.
	•	Print progress messages for transparency.
	•	Stop processing if critical columns (GL Code, total_adjusted_value) are missing.
	•	For removing empty columns, use: df = df.dropna(axis=1, how='all')
	•	For trimming column names, use: df.columns = df.columns.str.strip()
	•	Avoid using .eq() method on Index objects - use comparison operators instead

CRITICAL CONSTRAINTS
	•	Output must contain exactly all GL Codes from trial balance.
	•	**GL Code Matching**: MUST convert both sides to lowercase strings before comparison: str(code).strip().lower()
	•	This is CRITICAL - without lowercase conversion, codes like "34010000L" will not match "34010000l"
	•	Generate issue file for any anomalies.

EXAMPLE OUTPUT STRUCTURE
Main Output File:
GL Code     | Adj3_RF
84036000    | 0.0
14010080    | 750.0
14050067    | 0.0

Issue Report File:
Row Number  | Issue Type            | Details
18          | Missing GL Code       | GL Code not found in source
41          | Invalid Numeric Data  | Value: "???" in adjustment

QUALITY ASSURANCE CHECKLIST
Before finalizing:
	1	File Integrity – Both input files load without errors.
	2	Data Cleaning Applied – Empty rows removed, headers normalized.
	3	Issue File Generated – All anomalies logged.
	4	GL Code Coverage – Output includes all trial balance GL Codes.
	5	Numeric Conversion Verified – No strings left in numeric columns.
	6	Output Structure – Only "GL Code" and "Adj3_RF" in main file.
	7	File Naming & Location – Matches specified paths.
	8	Progress Logging – Console confirms each major step.
"""


# Prompt for Adjustment #4 - Interco Adjustments
PROMPT_INTERCO_ADJUSTMENTS = """Prompt for Adjustment #4 – Intercompany Adjustments

BUSINESS CONTEXT
Intercompany adjustments ensure that transactions between related entities are properly reconciled and eliminated where necessary. This process prevents double counting, maintains accurate consolidated financial statements, and ensures compliance with group reporting standards and audit requirements.

OBJECTIVE
Process Adjustment #4 by:
	•	Matching GL Codes between the source trial balance and the intercompany adjustment file.
	•	Generating:
	◦	A clean output file with intercompany adjustment amounts for each GL Code.
	◦	An issue report file highlighting anomalies or data quality problems.

INPUT FILES
	1	unadjusted_trialbalance.xlsx 
	◦	Location: unadjusted-trialbalance directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"(Unaudited) Mar'25"
	2	interco_manual_adjustments.xlsx 
	◦	Location: manual-adjustments directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"Interco Adjustment"
	▪	"total_adjusted_value"

COLUMN NAME ALIASES
	•	"GL Description" and "GL Code Description" are the same field and should be treated as interchangeable
	•	When searching for description columns, check for both variations
	•	Normalize column names during data loading to handle variations

PROCESSING RULES
Step 1: Data Validation & Cleaning
	•	Remove empty rows and columns.
	•	Detect and ignore extra header rows (check if GL Code column contains non-numeric or repeated header text).
	•	Drop summary or total rows (detect keywords like "Total", "Summary").
	•	Normalize:
	◦	Trim whitespace in GL Codes.
	◦	**CRITICAL**: Convert ALL GL Codes to strings using str(), then convert to lowercase using .lower() for comparison.
	◦	This ensures GL codes like "34010000L" match with "34010000l" and numeric codes like 21035438 match with "21035438".
	◦	Convert numeric columns to float (handle strings, remove junk characters like commas or currency symbols).
	•	Round excessive decimal places (e.g., to 2 or 4 decimals).
	•	Flag:
	◦	Missing GL Codes.
	◦	Invalid numeric formats.
	◦	Unrecognizable characters or corrupted cells.
Step 2: Matching Logic
	•	**CRITICAL GL Code Matching Requirements**:
	◦	Convert ALL GL Codes to strings: str(gl_code).strip().lower()
	◦	This must be done for BOTH trial balance and adjustment file GL codes
	◦	Create lookup dictionaries using lowercase string GL codes as keys
	◦	Example: interco_dict[str(gl_code).strip().lower()] = value
	•	For each GL Code in unadjusted_trialbalance.xlsx:
	◦	Normalize to lowercase string: gl_key = str(gl_code).strip().lower()
	◦	Match with normalized GL Code in interco_manual_adjustments.xlsx using: gl_key in interco_dict
	◦	If match found: use "total_adjusted_value".
	◦	If no match: assign 0.0.
	◦	If match found: use "total_adjusted_value".
	◦	If no match: assign 0.0.
Step 3: Output Files
	•	Main Output File:
	◦	Name: interco_adjustments_reconciliation.xlsx
	◦	Columns:
	◦	"GL Code"
	◦	"Adj4_INTERCO"
	◦	Include all GL Codes from trial balance (no missing rows).
	•	Issue Report File:
	◦	Name: interco_adjustments_issues.xlsx
	◦	Columns:
	◦	"Row Number"
	◦	"Issue Type" (e.g., Missing GL Code, Invalid Numeric Format)
	◦	"Details"

OUTPUT REQUIREMENTS
	•	Adjustment values must be numeric (float).
	•	No extra columns or descriptions in the main output.
	•	Ensure file paths match output_file variable.

PYTHON IMPLEMENTATION REQUIREMENTS
	•	Use pandas for data processing.
	•	Reference file paths from SOURCE_FILES_DIR and MANUAL_ADJUSTMENTS_DIR.
	•	Implement:
	◦	Data cleaning.
	◦	Issue logging.
	◦	Matching logic.
	•	Print progress messages for transparency.
	•	Stop processing if critical columns (GL Code, total_adjusted_value) are missing.
	•	For removing empty columns, use: df = df.dropna(axis=1, how='all')
	•	For trimming column names, use: df.columns = df.columns.str.strip()
	•	Avoid using .eq() method on Index objects - use comparison operators instead

CRITICAL CONSTRAINTS
	•	Output must contain exactly all GL Codes from trial balance.
	•	**GL Code Matching**: MUST convert both sides to lowercase strings before comparison: str(code).strip().lower()
	•	This is CRITICAL - without lowercase conversion, codes like "34010000L" will not match "34010000l"
	•	Generate issue file for any anomalies.

EXAMPLE OUTPUT STRUCTURE
Main Output File:
GL Code     | Adj4_INTERCO
84036000    | 0.0
14010080    | 200.0
14050067    | 0.0

Issue Report File:
Row Number  | Issue Type            | Details
20          | Missing GL Code       | GL Code not found in source
45          | Invalid Numeric Data  | Value: "###" in adjustment

QUALITY ASSURANCE CHECKLIST
Before finalizing:
	1	File Integrity – Both input files load without errors.
	2	Data Cleaning Applied – Empty rows removed, headers normalized.
	3	Issue File Generated – All anomalies logged.
	4	GL Code Coverage – Output includes all trial balance GL Codes.
	5	Numeric Conversion Verified – No strings left in numeric columns.
	6	Output Structure – Only "GL Code" and "Adj4_INTERCO" in main file.
	7	File Naming & Location – Matches specified paths.
	8	Progress Logging – Console confirms each major step.
"""


# Prompt for Adjustment #5 - Audit Adjustment Entries Proposed by GT India
PROMPT_GT_INDIA_AUDIT_ADJUSTMENTS = """Prompt for Adjustment #5 – Audit Adjustment Entries Proposed by GT India

BUSINESS CONTEXT
This adjustment incorporates audit entries proposed by Grant Thornton India to ensure compliance with audit recommendations and accurate financial reporting. These adjustments correct misstatements identified during the audit process, supporting transparency, regulatory compliance, and audit readiness.

OBJECTIVE
Process Adjustment #5 by:
	•	Matching GL Codes between the source trial balance and the GT India audit adjustment file.
	•	Generating:
	◦	A clean output file with adjustment amounts for each GL Code.
	◦	An issue report file highlighting anomalies or data quality problems.

INPUT FILES
	1	unadjusted_trialbalance.xlsx 
	◦	Location: unadjusted-trialbalance directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"(Unaudited) Mar'25"
	2	audit_adjustment_entries.xlsx 
	◦	Location: manual-adjustments directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"GT Audit Adj: 22-23"
	▪	"GT Audit Adj: 23-24"
	▪	"GT Audit Adj: 24-25"
	▪	"total_adjusted_value"

COLUMN NAME ALIASES
	•	"GL Description" and "GL Code Description" are the same field and should be treated as interchangeable
	•	When searching for description columns, check for both variations
	•	Normalize column names during data loading to handle variations

PROCESSING RULES
Step 1: Data Validation & Cleaning
	•	Remove empty rows and columns.
	•	Detect and ignore extra header rows (check if GL Code column contains non-numeric or repeated header text).
	•	Drop summary or total rows (detect keywords like "Total", "Summary").
	•	Normalize:
	◦	Trim whitespace in GL Codes.
	◦	**CRITICAL**: Convert ALL GL Codes to strings using str(), then convert to lowercase using .lower() for comparison.
	◦	This ensures GL codes like "34010000L" match with "34010000l" and numeric codes like 21035438 match with "21035438".
	◦	Convert numeric columns to float (handle strings, remove junk characters like commas or currency symbols).
	•	Round excessive decimal places (e.g., to 2 or 4 decimals).
	•	Flag:
	◦	Missing GL Codes.
	◦	Invalid numeric formats.
	◦	Unrecognizable characters or corrupted cells.
Step 2: Matching Logic
	•	**CRITICAL GL Code Matching Requirements**:
	◦	Convert ALL GL Codes to strings: str(gl_code).strip().lower()
	◦	This must be done for BOTH trial balance and adjustment file GL codes
	◦	Create lookup dictionaries using lowercase string GL codes as keys
	◦	Example: gt_dict[str(gl_code).strip().lower()] = value
	•	For each GL Code in unadjusted_trialbalance.xlsx:
	◦	Normalize to lowercase string: gl_key = str(gl_code).strip().lower()
	◦	Match with normalized GL Code in audit_adjustment_entries.xlsx using: gl_key in gt_dict
	◦	If match found: use "total_adjusted_value".
	◦	If no match: assign 0.0.
	◦	If match found: use "total_adjusted_value".
	◦	If no match: assign 0.0.
Step 3: Output Files
	•	Main Output File:
	◦	Name: gt_india_audit_adjustments_reconciliation.xlsx
	◦	Columns:
	◦	"GL Code"
	◦	"Adj5_GT"
	◦	Include all GL Codes from trial balance (no missing rows).
	•	Issue Report File:
	◦	Name: gt_india_audit_adjustments_issues.xlsx
	◦	Columns:
	◦	"Row Number"
	◦	"Issue Type" (e.g., Missing GL Code, Invalid Numeric Format)
	◦	"Details"

OUTPUT REQUIREMENTS
	•	Adjustment values must be numeric (float).
	•	No extra columns or descriptions in the main output.
	•	Ensure file paths match output_file variable.

PYTHON IMPLEMENTATION REQUIREMENTS
	•	Use pandas for data processing.
	•	Reference file paths from SOURCE_FILES_DIR and MANUAL_ADJUSTMENTS_DIR.
	•	Implement:
	◦	Data cleaning.
	◦	Issue logging.
	◦	Matching logic.
	•	Print progress messages for transparency.
	•	Stop processing if critical columns (GL Code, total_adjusted_value) are missing.
	•	For removing empty columns, use: df = df.dropna(axis=1, how='all')
	•	For trimming column names, use: df.columns = df.columns.str.strip()
	•	Avoid using .eq() method on Index objects - use comparison operators instead

CRITICAL CONSTRAINTS
	•	Output must contain exactly all GL Codes from trial balance.
	•	**GL Code Matching**: MUST convert both sides to lowercase strings before comparison: str(code).strip().lower()
	•	This is CRITICAL - without lowercase conversion, codes like "34010000L" will not match "34010000l"
	•	Generate issue file for any anomalies.

EXAMPLE OUTPUT STRUCTURE
Main Output File:
GL Code     | Adj5_GT
84036000    | 0.0
14010080    | -1200.0
14050067    | 0.0

Issue Report File:
Row Number  | Issue Type            | Details
22          | Missing GL Code       | GL Code not found in source
47          | Invalid Numeric Data  | Value: "???" in adjustment

QUALITY ASSURANCE CHECKLIST
Before finalizing:
	1	File Integrity – Both input files load without errors.
	2	Data Cleaning Applied – Empty rows removed, headers normalized.
	3	Issue File Generated – All anomalies logged.
	4	GL Code Coverage – Output includes all trial balance GL Codes.
	5	Numeric Conversion Verified – No strings left in numeric columns.
	6	Output Structure – Only "GL Code" and "Adj5_GT" in main file.
	7	File Naming & Location – Matches specified paths.
	8	Progress Logging – Console confirms each major step.
"""


# Prompt for Adjustment #6 - Reclassification Entries Proposed by GT India
PROMPT_RECLASSIFICATION_ENTRIES_ADJUSTMENTS = """Prompt for Adjustment #6 – Reclassification Entries Proposed by GT India

BUSINESS CONTEXT
Reclassification entries ensure that amounts are presented under the correct financial statement line items. These adjustments are proposed by Grant Thornton India to align with accounting standards and improve clarity in reporting. This process supports accurate classification, compliance, and audit readiness.

OBJECTIVE
Process Adjustment #6 by:
	•	Matching GL Codes between the source trial balance and the reclassification adjustment file.
	•	Generating:
	◦	A clean output file with reclassification adjustment amounts for each GL Code.
	◦	An issue report file highlighting anomalies or data quality problems.

INPUT FILES
	1	unadjusted_trialbalance.xlsx 
	◦	Location: unadjusted-trialbalance directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"(Unaudited) Mar'25"
	2	reclass_entries_adjustments.xlsx 
	◦	Location: manual-adjustments directory
	◦	Expected Columns:
	▪	"GL Code"
	▪	"GL Description" (may also appear as "GL Code Description" - treat as interchangeable)
	▪	"Reclass: Mar'25"
	▪	"total_adjusted_value"

COLUMN NAME ALIASES
	•	"GL Description" and "GL Code Description" are the same field and should be treated as interchangeable
	•	When searching for description columns, check for both variations
	•	Normalize column names during data loading to handle variations

PROCESSING RULES
Step 1: Data Validation & Cleaning
	•	Remove empty rows and columns.
	•	Detect and ignore extra header rows (check if GL Code column contains non-numeric or repeated header text).
	•	Drop summary or total rows (detect keywords like "Total", "Summary").
	•	Normalize:
	◦	Trim whitespace in GL Codes.
	◦	**CRITICAL**: Convert ALL GL Codes to strings using str(), then convert to lowercase using .lower() for comparison.
	◦	This ensures GL codes like "34010000L" match with "34010000l" and numeric codes like 21035438 match with "21035438".
	◦	Convert numeric columns to float (handle strings, remove junk characters like commas or currency symbols).
	•	Round excessive decimal places (e.g., to 2 or 4 decimals).
	•	Flag:
	◦	Missing GL Codes.
	◦	Invalid numeric formats.
	◦	Unrecognizable characters or corrupted cells.
Step 2: Matching Logic
	•	**CRITICAL GL Code Matching Requirements**:
	◦	Convert ALL GL Codes to strings: str(gl_code).strip().lower()
	◦	This must be done for BOTH trial balance and adjustment file GL codes
	◦	Create lookup dictionaries using lowercase string GL codes as keys
	◦	Example: reclass_dict[str(gl_code).strip().lower()] = value
	•	For each GL Code in unadjusted_trialbalance.xlsx:
	◦	Normalize to lowercase string: gl_key = str(gl_code).strip().lower()
	◦	Match with normalized GL Code in reclass_entries_adjustments.xlsx using: gl_key in reclass_dict
	◦	If match found: use "total_adjusted_value".
	◦	If no match: assign 0.0.
Step 3: Output Files
	•	Main Output File:
	◦	Name: reclass_entries_reconciliation.xlsx
	◦	Columns:
	◦	"GL Code"
	◦	"Adj6_RECLASS"
	◦	Include all GL Codes from trial balance (no missing rows).
	•	Issue Report File:
	◦	Name: reclass_entries_issues.xlsx
	◦	Columns:
	◦	"Row Number"
	◦	"Issue Type" (e.g., Missing GL Code, Invalid Numeric Format)
	◦	"Details"

OUTPUT REQUIREMENTS
	•	Adjustment values must be numeric (float).
	•	No extra columns or descriptions in the main output.
	•	Ensure file paths match output_file variable.

PYTHON IMPLEMENTATION REQUIREMENTS
	•	Use pandas for data processing.
	•	Reference file paths from SOURCE_FILES_DIR and MANUAL_ADJUSTMENTS_DIR.
	•	Implement:
	◦	Data cleaning.
	◦	Issue logging.
	◦	Matching logic.
	•	Print progress messages for transparency.
	•	Stop processing if critical columns (GL Code, total_adjusted_value) are missing.
	•	For removing empty columns, use: df = df.dropna(axis=1, how='all')
	•	For trimming column names, use: df.columns = df.columns.str.strip()
	•	Avoid using .eq() method on Index objects - use comparison operators instead

CRITICAL CONSTRAINTS
	•	Output must contain exactly all GL Codes from trial balance.
	•	**GL Code Matching**: MUST convert both sides to lowercase strings before comparison: str(code).strip().lower()
	•	This is CRITICAL - without lowercase conversion, codes like "34010000L" will not match "34010000l"
	•	Generate issue file for any anomalies.

EXAMPLE OUTPUT STRUCTURE
Main Output File:
GL Code     | Adj6_RECLASS
84036000    | 0.0
14010080    | 500.0
14050067    | 0.0

Issue Report File:
Row Number  | Issue Type            | Details
25          | Missing GL Code       | GL Code not found in source
49          | Invalid Numeric Data  | Value: "###" in adjustment

QUALITY ASSURANCE CHECKLIST
Before finalizing:
	1	File Integrity – Both input files load without errors.
	2	Data Cleaning Applied – Empty rows removed, headers normalized.
	3	Issue File Generated – All anomalies logged.
	4	GL Code Coverage – Output includes all trial balance GL Codes.
	5	Numeric Conversion Verified – No strings left in numeric columns.
	6	Output Structure – Only "GL Code" and "Adj6_RECLASS" in main file.
	7	File Naming & Location – Matches specified paths.
	8	Progress Logging – Console confirms each major step.
"""
