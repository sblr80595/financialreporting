# NOTE 27: CHANGES IN INVENTORIES OF TRADED GOODS
**Period: (Unaudited) Jun'25**

---

## GL LEVEL BREAKDOWN FOR NOTE 27
**Period: (Unaudited) Jun'25**

### Closing Inventory Components (from Balance Sheet):

| GL Code | GL Description | Ind AS Minor | Closing Balance (₱) |
|---|---|---|---|
| 11301010 | Inventory - Reagents | Stock in Traded goods | 35,42,40,038.46 |
| 11301020 | Inventory - Consumables | Stock in Traded goods | 1,97,76,994.08 |
| 11301030 | Inventory - Laboratory Equipment | Stock in Traded goods | 9,90,98,140.59 |
| 11301040 | Inventory - Accessories and Bundles | Stock in Traded goods | 82,99,324.22 |
| 11301050 | Inventory - Software | Stock in Traded goods | 42,22,764.02 |
| 11301060 | Allowance for Inventory Obsolescence | Less allowance for inventory obsolescence | (38,93,426.85) |
| 11302010 | Inventory - Office Supplies | Stock in Traded goods | 5,40,692.78 |
| 11302020 | Inventory - Spareparts | Spare parts | 8,32,29,099.93 |
| 11304010 | Consignment Inventory - Reagents | Stock in Traded goods | 33,41,655.24 |
| 11304020 | Consignment Inventory - Consumables | Stock in Traded goods | 2,33,752.94 |
| 12401010 | Fixed Asset Clearing Account | Fixed Asset Clearing Account | 36,76,168.65 |

**Total Closing Inventory (All Components):** | | | **₱ 56,56,55,404.06** |

---

### Opening Inventory Components:

**Note:** The trial balance data provided contains ONLY closing balance information in the "Total June 2025" column. The opening balance values for these inventory accounts are NOT provided in the current dataset.

**Unable to Complete Full Calculation:** The instruction specifies using 'Opening Balance' and 'Closing Balance' columns from the trial balance, but the provided CSV data contains only:
- GL Code
- GL Code Description  
- Ind AS Minor
- Major category
- Minor category
- **Total June 2025** (which appears to be a period total, not Opening/Closing Balance columns)

---

## SUMMARY CALCULATION

**⚠️ DATA LIMITATION NOTICE:**

The trial balance data provided does NOT include separate "Opening Balance" and "Closing Balance" columns as required by the instructions. The only monetary column present is "Total June 2025," which appears to be a period transaction total rather than balance sheet opening/closing balances.

### Available Information:
**Closing Inventory (as of Jun 2025):**
- Stock in Traded goods: ₱ 48,91,32,607.33
- Spare parts: ₱ 8,32,29,099.93
- Fixed Asset Clearing Account: ₱ 36,76,168.65
- Less: Allowance for Inventory Obsolescence: (₱ 38,93,426.85)
- **Total Net Closing Inventory: ₱ 57,21,44,449.06**

**Opening Inventory:** 
- **NOT AVAILABLE** - Opening Balance column missing from dataset

---

## ERROR NOTIFICATION

**Cannot Generate Complete NOTE 27 as Specified**

**Reason:** The trial balance CSV provided lacks the mandatory opening and closing balance columns required for this note.

**To Complete This Note, Please Provide:**
1. A "Opening Balance" column containing opening inventory balances as of the beginning of the period
2. A "Closing Balance" column containing closing inventory balances as of Jun 2025
3. Confirmation that the current "Total June 2025" represents period transactions (not balances)

**Current Data Structure Issue:**
- The CSV contains only one monetary column: "Total June 2025"
- This appears to be a period total, NOT an opening or closing balance
- Cannot perform the required calculation: Net Change = (Opening Inventory - Closing Inventory)

---

### PLACEHOLDER OUTPUT (Cannot be finalized without Opening Balances):

**NOTE 27: CHANGES IN INVENTORIES OF TRADED GOODS**
**Period: (Unaudited) Jun'25**

| Particulars | Amount (₱) |
|---|---|
| **Inventories at the end of the period:** | |
| Traded goods and spare parts (net) | ₱ 57,21,44,449.06 |
| **Inventories at the beginning of the period:** | |
| Traded goods and spare parts (net) | **[OPENING BALANCE DATA NOT PROVIDED]** |
| **TOTAL CHANGES IN INVENTORIES OF TRADED GOODS** | **[CANNOT BE CALCULATED]** |

---

## RECOMMENDED ACTION

Please provide the trial balance with distinct **Opening Balance** and **Closing Balance** columns to enable accurate calculation of Changes in Inventories of Traded Goods per Ind AS and Schedule III requirements.

```json
{
  "note_number": "27",
  "note_title": "CHANGES IN INVENTORIES OF TRADED GOODS",
  "period": "(Unaudited) Jun'25",
  "error_status": "INCOMPLETE - OPENING BALANCE DATA MISSING",
  "closing_inventory_calculated": 5721444449.06,
  "opening_inventory_status": "NOT PROVIDED IN SOURCE DATA",
  "excel_data": [
    {
      "particulars": "ERROR: Cannot generate complete note without Opening Balance column",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Inventories at the end of the period:",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Traded goods and spare parts (net of obsolescence allowance)",
      "amount": 5721444449.06,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Inventories at the beginning of the period:",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "DATA NOT AVAILABLE - Opening Balance column missing",
      "amount": 0,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "TOTAL CHANGES IN INVENTORIES OF TRADED GOODS",
      "amount": 0,
      "is_bold": true,
      "is_total": true
    }
  ],
  "data_quality_issues": [
    "Missing 'Opening Balance' column in source data",
    "Missing 'Closing Balance' column in source data",
    "Only 'Total June 2025' period column available",
    "Cannot perform required calculation: (Opening - Closing) = Change"
  ]
}
```

**Status:** ❌ **INCOMPLETE - AWAITING CORRECTED TRIAL BALANCE DATA**