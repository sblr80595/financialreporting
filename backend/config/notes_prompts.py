"""
Financial note generation prompt templates.

This module contains prompt templates for AI-powered financial note generation
using Google Gemini. Templates are designed for Indian Accounting Standards
(Ind AS) and Schedule III compliance.

All templates now include MANDATORY structured output section for Excel generation.
"""

# Common structured output instructions for all templates
STRUCTURED_OUTPUT_INSTRUCTION = """

---

## CRITICAL: STRUCTURED OUTPUT FOR EXCEL GENERATION

**YOU MUST INCLUDE THIS EXACT SECTION AT THE END OF YOUR OUTPUT:**

After generating the complete note with GL breakdown and summary tables, you MUST add this section:

```json
{{
  "note_number": "[NOTE_NUMBER]",
  "note_title": "[NOTE_TITLE]",
  "period": "[PERIOD]",
  "excel_data": [
    {{
      "particulars": "[Line item description]",
      "amount": [numeric_value_without_currency],
      "is_bold": [true/false],
      "is_total": [true/false]
    }}
  ]
}}
```

**RULES FOR excel_data:**
1. Include ONLY the main summary table rows (NOT GL breakdown)
2. Each row must have: "particulars", "amount", "is_bold", "is_total"
3. Amount must be numeric (no ₹ symbol, no commas) - use negative for deductions
4. Set "is_bold": true for headers, totals, and section titles
5. Set "is_total": true ONLY for the final total row
6. Preserve the order of rows exactly as in the summary table
7. For header rows without amounts, set amount to 0
8. This JSON block is MANDATORY - the note is incomplete without it

**Example:**
```json
{{
  "note_number": "28",
  "note_title": "EMPLOYEE BENEFITS EXPENSE",
  "period": "Total Jun'25",
  "excel_data": [
    {{
      "particulars": "Employee Benefits Expense",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    }},
    {{
      "particulars": "Salaries and wages",
      "amount": 764458.20,
      "is_bold": false,
      "is_total": false
    }},
    {{
      "particulars": "Contributions to provident and other funds",
      "amount": 79231.80,
      "is_bold": false,
      "is_total": false
    }},
    {{
      "particulars": "Staff welfare expenses",
      "amount": 58157.69,
      "is_bold": false,
      "is_total": false
    }},
    {{
      "particulars": "TOTAL EMPLOYEE BENEFITS EXPENSE",
      "amount": 901847.69,
      "is_bold": true,
      "is_total": true
    }}
  ]
}}
```

**This structured data enables automatic Excel generation without parsing errors.**
"""

PROFIT_LOSS_TEMPLATE = """
You are an expert financial accountant specializing in Indian Accounting Standards (Ind AS) and Schedule III compliance.
Your sole task is to generate '{note_title}' for the Profit & Loss Statement from trial balance data.

## Currency Information:
**All monetary amounts in this note MUST be formatted using: {currency_symbol} ({currency_name})**
- Use {currency_symbol} symbol for all amounts (NOT ₹ unless specified)
- Follow proper formatting: {currency_symbol} 1,234.56
- Examples: {currency_symbol} 10,000.00, {currency_symbol} 1,23,456.78

## Input:
Trial balance CSV with columns:
- GL Code
- GL Code Description
- Ind AS Minor
- Period totals (e.g., 'Total Mar'25')

## IMPORTANT - Period Column to Use:
**You MUST use the column '{period_column}' for ALL calculations and amounts in this note.**
- Extract ALL values from the '{period_column}' column only
- Ignore all other period columns in the CSV
- If '{period_column}' is not found, report an error

## Core Responsibilities:
1. Read trial balance data.
2. Generate ONLY '{note_title}' for Profit & Loss Statement.
3. Present the output in a professional Schedule III compliant format.
4. Provide a detailed GL-level breakdown before the final summary note.
5. Use ONLY the '{period_column}' column for all amounts.
6. **MANDATORY**: Format all amounts with {currency_symbol} symbol.
7. **MANDATORY**: Include structured JSON output at the end for Excel generation.

---

## Data Processing Rules:
- **Filter strictly by 'Ind AS Minor' column** for the categories listed below. Use case-insensitive and whitespace-trimmed matching.
- **Period Column**: Extract values ONLY from the '{period_column}' column
- **Algebraic Summation**: {summation_rule}
- **CRITICAL CURRENCY FORMATTING**: 
  * EVERY monetary amount MUST be prefixed with {currency_symbol} symbol
  * Format: {currency_symbol} 1,234.56 (with space after symbol)
  * Example: {currency_symbol} 16,692.38, {currency_symbol} 78,201.74, {currency_symbol} 9,04,025.90
  * Never show amounts without the {currency_symbol} symbol
  * If a category has no entries, display it as {currency_symbol} 0 or {currency_symbol} 0.00
- **Structure**: The final output must first show the GL-level detail and then the final summary table. Ensure the summary total reconciles with the GL breakdown.

---

## {note_number}: {note_title_upper}
**Categories to include (filter by 'Ind AS Minor'):**
{categories_list}

**Required Output Format:**

**GL Level Breakdown for {note_number}**
**Period: {period_column}**
| GL Code | GL Description | Amount ({currency_symbol}) |
|---|---|---|
| ... | ... | ... |
**Total:** | | **{currency_symbol} [Total from GLs]** |

---

**{note_number}: {note_title_upper}**
**Period: {period_column}**
| Particulars | Amount ({currency_symbol}) |
|---|---|
{output_rows}
| **TOTAL {note_title_upper}** | **{currency_symbol} [Grand Total]** |

{additional_instructions}

""" + STRUCTURED_OUTPUT_INSTRUCTION

BALANCE_SHEET_TEMPLATE = """
You are an expert financial accountant specializing in Indian Accounting Standards (Ind AS) and Schedule III compliance.
Your sole task is to generate '{note_title}' for the Balance Sheet from trial balance data.

## Currency Information:
**All monetary amounts in this note MUST be formatted using: {currency_symbol} ({currency_name})**
- Use {currency_symbol} symbol for all amounts (NOT ₹ unless specified)
- Follow proper formatting: {currency_symbol} 1,234.56
- Examples: {currency_symbol} 10,000.00, {currency_symbol} 1,23,456.78

## Input:
Trial balance CSV with columns:
- GL Code
- GL Code Description
- Ind AS Minor
- Period totals (e.g., 'Total Jun'25')

## IMPORTANT - Period Column to Use:
**You MUST use the column '{period_column}' for ALL calculations and amounts in this note.**
- Extract ALL values from the '{period_column}' column only
- Ignore all other period columns in the CSV
- If '{period_column}' is not found, report an error

## Core Responsibilities:
1. Read trial balance data.
2. Generate ONLY '{note_title}' for Balance Sheet.
3. Present the output in a professional Schedule III compliant format.
4. Provide a detailed GL-level breakdown before the final summary note.
5. Use ONLY the '{period_column}' column for all amounts.
6. **MANDATORY**: Format all amounts with {currency_symbol} symbol.
7. **MANDATORY**: Include structured JSON output at the end for Excel generation.

---

## Data Processing Rules:
- **Filter strictly by 'Ind AS Minor' column** for the categories listed below. Use case-insensitive and whitespace-trimmed matching.
- **Period Column**: Extract values ONLY from the '{period_column}' column
- **Value Extraction**: {summation_rule}
- **CRITICAL CURRENCY FORMATTING**: 
  * EVERY monetary amount MUST be prefixed with {currency_symbol} symbol
  * Format: {currency_symbol} 1,234.56 (with space after symbol)
  * Example: {currency_symbol} 16,692.38, {currency_symbol} 78,201.74, {currency_symbol} 9,04,025.90
  * Never show amounts without the {currency_symbol} symbol
  * If a category has no entries, display it as {currency_symbol} 0 or {currency_symbol} 0.00
- **Structure**: The final output must first show the GL-level detail and then the final summary table. Ensure the summary total reconciles with the GL breakdown.
- **Subtotals and Deductions**: Handle subtotals and deduction items (like "Less: Provision") as specified in the output format.
- **Sign Handling**:
  - Items with `sign_flip: true` - Reverse the sign of the value (if negative, make positive; if positive, make negative)
  - Items with `is_deduction: true` and `display_format: "-(value)"` - Show value in parentheses as: ({currency_symbol} amount) or -({currency_symbol} amount)

---

## {note_number}: {note_title_upper}
**Categories to include (filter by 'Ind AS Minor'):**
{categories_list}

**Required Output Format:**

**GL Level Breakdown for {note_number}**
**Period: {period_column}**
| GL Code | GL Description | Amount ({currency_symbol}) |
|---|---|---|
| ... | ... | {currency_symbol} ... |
**Total:** | | **{currency_symbol} [Total from GLs]** |

---

**{note_number}: {note_title_upper}**
**Period: {period_column}**
| Particulars | Amount ({currency_symbol}) |
|---|---|
{output_rows}

{additional_instructions}

---

## Important Notes:
- **CRITICAL**: ALL amounts MUST include the {currency_symbol} symbol (e.g., {currency_symbol} 16,692.38)
- For items marked with "refer note below", include this text in the Particulars column.
- For deduction items (starting with "Less:"), show amounts in parentheses: ({currency_symbol} amount)
- For headers (marked with **), display without amounts.
- For items with `sign_flip: true`, reverse the sign before displaying.
- Calculate subtotals and final totals according to the specified calculation rules.
- Ensure all amounts are properly formatted with {currency_symbol} symbol.
- Asset categories typically have debit balances (positive values).
- Liability and provision categories may have credit balances (negative in trial balance, present as positive).
- The same category may be used multiple times with different sign handling as specified in the configuration.

""" + STRUCTURED_OUTPUT_INSTRUCTION

IMPORTANT_NOTES_TEMPLATE = """
You are an expert financial accountant specializing in Indian Accounting Standards (Ind AS) and Schedule III compliance.
Your task is to generate '{note_title}' from multiple data sources including trial balance and auxiliary files.

## Input:
1. Trial balance CSV with columns: GL Code, GL Code Description, BSPL, Ind AS Major, Ind AS Minor, period totals
2. Auxiliary data files (as specified in configuration)

## Core Responsibilities:
1. Read and process trial balance data and auxiliary files.
2. Generate ONLY '{note_title}' with multi-period analysis if required.
3. Present the output in a professional Schedule III compliant format.
4. Provide detailed GL-level breakdown before the final summary.
5. Include reconciliation and analysis sections as specified.
6. **MANDATORY**: Include structured JSON output at the end for Excel generation.

---

## Data Processing Rules:
- **Filter by 'Ind AS Minor' column** for the categories listed below. Use case-insensitive and whitespace-trimmed matching.
- **Multi-source Integration**: {multi_source_rule}
- **Algebraic Summation**: {summation_rule}
- **Formatting**: Format all amounts in the Indian Rupee style (e.g., ₹1,23,456). If a category has no entries, display it as ₹0.
- **Structure**: The final output must include:
  1. GL-level detail breakdown
  2. Summary table(s) for each period
  3. Reconciliation sections (if applicable)
- **Period Handling**: {period_handling}

---

## {note_number}: {note_title_upper}
**Categories to include (filter by 'Ind AS Minor'):**
{categories_list}

**Auxiliary Data Sources:**
{auxiliary_sources}

**Required Output Format:**

### 1. GL Level Breakdown for {note_number}
{gl_breakdown_format}

---

### 2. Summary Table: {note_title_upper}
{summary_table_format}

---

### 3. Reconciliation/Analysis Section
{reconciliation_format}

{additional_instructions}

---

## Important Notes:
- For multi-period notes, generate separate sections for each period.
- Ensure all calculations are algebraically correct (preserve signs).
- Cross-reference auxiliary data with trial balance for validation.
- Include comparative analysis if multiple periods are present.
- Round amounts consistently (no decimals unless specified).
- Highlight any discrepancies or balancing figures clearly.

""" + STRUCTURED_OUTPUT_INSTRUCTION

CASH_FLOW_TEMPLATE = """
You are an expert financial accountant specializing in Indian Accounting Standards (Ind AS) and Schedule III compliance.
Your task is to generate '{note_title}' (Cash Flow Statement - Indirect Method) that EXACTLY matches the reference format.

## Input:
1. Trial balance CSV with columns: GL Code, GL Code Description, BSPL, Ind AS Major, Ind AS Minor, period totals
2. Auxiliary data files (if specified)

## CRITICAL - Period Column to Use:
**You MUST use the column '{period_column}' for ALL current year calculations.**
**You MUST use the column '{prior_period_column}' for working capital movement calculations.**
- Extract current year values from '{period_column}' ONLY
- Calculate working capital changes: {period_column} - {prior_period_column}
- Ignore all other period columns

---

## EXACT OUTPUT FORMAT REQUIRED

Generate TWO sections:

### SECTION 1: GL LEVEL BREAKDOWN

**GL Level Breakdown for {note_number}**
**Period: {period_column}** | **Prior Period: {prior_period_column}**

#### **A. Cash flow from operating activities**

| GL Code | GL Description | Ind AS Minor | Amount (₹) |
| :--- | :--- | :--- | :--- |
| **Profit before tax** | | | **[Amount]** |
| **Adjustments for:** | | | |
| [GL] | [Description] | [Ind AS Minor] | [Amount] |
| [GL] | [Description] | [Ind AS Minor] | [Amount] |
| ... for each adjustment item ... |
| *Sub-total: [subtotal name]* | | | *[Amount]* |
| **Operating profit before working capital changes** | | | **[Amount]** |
| **Changes in working Capital** | | | |
| [Description of movement] | | | [Amount] |
| ... for each working capital item ... |
| **Net cash flow from/(used in) operations before tax** | | | **[Amount]** |
| **Income tax refund/paid (net)** | | | **([Amount])** |
| **Net cash flows/ (used in) operating activities (A)** | | | **[Amount]** |

#### **B. Cash flows from investing activities**

| GL Code | GL Description | Ind AS Minor | Amount (₹) |
| :--- | :--- | :--- | :--- |
| **[Line item]** | | [Source] | ([Amount]) or [Amount] |
| ... for each investing item ... |
| **Net cash generated from /(used in) investing activities (B)** | | | **[Amount]** |

#### **C. Cash flows from financing activities**

| GL Code | GL Description | Ind AS Minor | Amount (₹) |
| :--- | :--- | :--- | :--- |
| **[Line item]** | | [Source] | [Amount] or ([Amount]) |
| ... for each financing item ... |
| **Net cash generated from /(used in) financing activities (C)** | | | **[Amount]** |

#### **Reconciliation of Cash and Cash Equivalents**

| GL Code | GL Description | Ind AS Minor | Amount (₹) |
| :--- | :--- | :--- | :--- |
| **Net Increase/(Decrease) in Cash and Cash Equivalents (A+B+C)** | | | **[Amount]** |
| **Cash and Cash Equivalents at Beginning of Period ({prior_period_column})** | | | **[Amount]** |
| **Calculated Cash and Cash Equivalents at End of Period** | | | **[Amount]** |
| **Actual Cash and Cash Equivalents at End of Period ({period_column})** | | | **[Amount]** |
| **Difference** | | | **[Amount if any]** |

---

### SECTION 2: CASH FLOW STATEMENT (FINAL FORMAT)

**{note_number}: CASH FLOW STATEMENT (INDIRECT METHOD)**
**For the period ending: {period_column}**

# CASH FLOW STATEMENT (INDIRECT METHOD)
## For the period ending: {period_column}

| Particulars | Amount (₹) |
| :--- | :--- |
| **Cash flow from operating activities** | |
| Profit before tax | [Amount] |
| **Adjustments for:** | |
{operating_adjustments}
| **Operating profit before working capital changes** | **[Amount]** |
| | |
| **Changes in working Capital** | |
{working_capital_changes}
| | |
| **Net cash flow from/(used in) operations before tax** | **[Amount]** |
| Income tax refund/paid (net) | ([Amount]) |
| **Net cash flows/ (used in) operating activities (A)** | **[Amount]** |
| | |
| **Cash flows from investing activities** | |
{investing_items}
| **Net cash generated from /(used in) investing activities (B)** | **[Amount]** |
| | |
| **Cash flows from financing activities** | |
{financing_items}
| **Net cash generated from /(used in) financing activities (C)** | **[Amount]** |
| | |
| Cash and cash equivalents of subsidiaries acquired (D) | [Amount or 0] |
| | |
| **Net increase/(decrease) in cash and cash equivalents (A+B+C+D)** | **[Amount]** |
| Cash and cash equivalents at the beginning of the year | [Amount] |
| **Cash and cash equivalents at the end of the period** | **[Amount]** |
| | |
| **Cash and cash equivalents include (refer note 13)** | |
| Cash on hand | [Amount] |
| Balance with banks | |
| - On current accounts | [Amount] |
| - Deposits with original maturity of less than three months | [Amount] |
| | |
| **Non- cash financing and investing activities:** | |
| - Acquisition of right-of-use assets | [Amount] |

---

## DATA PROCESSING RULES

### Operating Activities Categories:
{operating_adjustments}

### Working Capital Changes:
Calculate as: Current Period - Prior Period
{working_capital_changes}

### Investing Activities:
{investing_items}

### Financing Activities:
{financing_items}

---

## FORMATTING RULES

1. **Amount Format**: Indian Rupee style: ₹1,23,45,678
2. **Negative/Outflow**: Show in brackets: (₹12,34,567) or as negative
3. **Bold Items**: 
   - Section headers
   - "Operating profit before working capital changes"
   - "Net cash flow from/(used in) operations before tax"
   - All section totals (A), (B), (C)
   - Final reconciliation totals
4. **Italic Items**: Sub-totals in GL breakdown (e.g., *Sub-total: Depreciation*)
5. **Line Items**:
   - Use EXACT wording from config
   - Working capital: "(Decrease)/Increase" or "(Increase)/Decrease" format
   - Match reference image format precisely

---

## CRITICAL MATCHING REQUIREMENTS

**You MUST match the reference format EXACTLY:**

1. ✓ Section A title: "Cash flow from operating activities"
2. ✓ First line: "Profit before tax" (NOT "Profit/(Loss) before tax")
3. ✓ Adjustment header: "Adjustments for:" (bold, colon included)
4. ✓ Subtotal: "Operating profit before working capital changes" (bold)
5. ✓ WC Section: "Changes in working Capital" (capital 'C')
6. ✓ WC Items: Use format like "(Decrease) in trades payables" 
7. ✓ Operations subtotal: "Net cash flow from/(used in) operations before tax"
8. ✓ Tax line: "Income tax refund/paid (net)" with negative in brackets
9. ✓ Section total: "Net cash flows/ (used in) operating activities (A)"
10. ✓ Section B: "Cash flows from investing activities"
11. ✓ Section C: "Cash flows from financing activities"
12. ✓ Final total: "Net increase/(decrease) in cash and cash equivalents (A+B+C+D)"
13. ✓ Opening: "Cash and cash equivalents at the beginning of the year"
14. ✓ Closing: "Cash and cash equivalents at the end of the period"
15. ✓ Breakdown title: "Cash and cash equivalents include (refer note 13)"

---

## VALIDATION CHECKLIST

Before finalizing, verify:
- [ ] All GL codes mapped correctly to line items
- [ ] Period column '{period_column}' used for all current values
- [ ] Prior period '{prior_period_column}' used for WC calculations
- [ ] Working capital movements calculated correctly (current - prior)
- [ ] Asset increases shown as negative, decreases as positive
- [ ] Liability increases shown as positive, decreases as negative
- [ ] All outflows in brackets or negative
- [ ] Section totals sum correctly: A + B + C (+D) = Net Change
- [ ] Opening + Net Change = Closing cash
- [ ] Closing cash matches Balance Sheet
- [ ] Format matches reference image exactly
- [ ] **MANDATORY JSON output included at the end**

---

## AUXILIARY DATA SOURCES
{auxiliary_sources}

---

## OUTPUT STRUCTURE
{output_structure}

---

{additional_instructions}

---

**REMEMBER**: Your output must be IDENTICAL in structure and format to the reference cash flow statement provided. Every line item, every bracket, every bold/italic formatting must match exactly.

""" + STRUCTURED_OUTPUT_INSTRUCTION