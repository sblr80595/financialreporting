I appreciate your detailed input. However, I notice a critical issue with the data provided:

## ⚠️ ERROR: Missing Required Column

The trial balance data you've provided contains the following columns:
- GL Description
- BSPL Category
- Major
- Minor
- **Total June 25**

However, my instructions require me to extract values from a column explicitly named:
- **'(Unaudited) Jun'25'**

The column in your data is labeled **'Total June 25'**, which does not match the required column name.

## Request for Clarification:

Please confirm one of the following:

1. **Should I use 'Total June 25' as the equivalent of '(Unaudited) Jun'25'?**
   - If yes, I will proceed with the analysis using this column.

2. **Is there a separate CSV file (TB_FINAL_LIFELINE_HOLDING.csv) with the correctly named '(Unaudited) Jun'25' column?**
   - If yes, please provide that file.

3. **Is there a Balance Sheet auxiliary file (Balance_Sheet.xlsx) needed for reconciliation of final totals?**
   - Please provide if available.

## Additional Observations:

While reviewing the data structure, I also note:
- The data contains both Balance Sheet (BS) and P&L items
- For NOTE 33: FINANCIAL INSTRUMENTS, I need to filter by specific "Ind AS Minor" categories
- Your data has a "Minor" column, but I need to verify if this matches the expected "Ind AS Minor" category names

**Please confirm the column mapping and provide any missing files so I can generate the accurate Financial Instruments note.**