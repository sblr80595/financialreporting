# NOTE 35: RELATED PARTY DISCLOSURES
**Period: Total June 2025**

---

## GL LEVEL BREAKDOWN FOR NOTE 35

**Important Note:** After thorough review of the provided trial balance data, I must report that:

**No GL entries were found matching the 'Ind AS Minor' categories specified for Related Party Disclosures.**

The trial balance provided does not contain any line items with the following 'Ind AS Minor' descriptions:
- "Lifeline Holdings, Inc."
- "Everlife Holdings Pte Limited"
- "CPC Diagnostics Pvt Ltd."
- "Everlife Philippines Holding, Inc."
- "Artic GmbH, Germany"
- "Translumina France"
- "LAMED Vertriebsgesellschaft"
- "Blue Medical Devices BV"
- "Chemopharm SDN BHD"
- "Chemoscience Phils. Inc."
- "MPHP Punita Sharma"
- "Mr. Gurmit Singh Chugh"
- "Mr. Vishal Sharma"
- "Mr. Avnish Mehra"
- "Mr. Arjun Oberoi"
- "Mr. Vishal Goenka"
- "Mr. Indranil Mukherjee"
- "Rex A.Tiri"
- And other Related Party transaction/balance categories

---

## GL LEVEL BREAKDOWN TABLE

| GL Code | GL Description | Amount (₹) |
|---|---|---|
| **No Related Party GL entries found** | - | - |
| **Total:** | | **₹0** |

---

## NOTE 35: RELATED PARTY DISCLOSURES
**Period: Total June 2025**

| Particulars | Amount (₹) |
|---|---|
| **(A) Names of related parties and related party relationship** | |
| Related parties where control exists | ₹0 |
| Fellow Subsidiaries | ₹0 |
| Key Management Personnel ('KMP') | ₹0 |
| | |
| **(B) Transactions with related parties** | |
| Transactions during the year (Management Fees, Rent, etc.) | ₹0 |
| | |
| **(C) Balances outstanding at year end** | |
| Balances (Receivables, Payables, ROU Assets) | ₹0 |
| **TOTAL RELATED PARTY DISCLOSURES** | **₹0** |

---

## DATA QUALITY OBSERVATION

The trial balance provided contains the 'Ind AS Minor' column; however, the values in this column for the majority of entries are:
- **"Traded goods"** (for revenue and purchase items)
- **"Bank Balance"**, **"Cash"**, **"Inventories"** (for balance sheet items)
- **"Salaries, wages and Bonus"**, **"Employee benefits expense"** (for employee-related items)
- **"Depreciation and amortisation expense"** (for asset-related items)
- Other standard accounting categories

**None of these entries correspond to the Related Party categories specified in the instructions.**

### **Possible Reasons:**
1. The Related Party transaction data may be maintained in a separate subsidiary ledger or supplementary schedule (as referenced in the instructions: "Data is in PHP (Pesos). Columns represent years ended 31 March 2025, 2024, and 2023. Ensure KMP list combines both the definition section and those appearing in transactions").
2. The Related Party information may be contained in the file **ttpl_impnotes.csv** (referenced in the instructions) rather than the main trial balance.
3. Related Party transactions may have been eliminated or consolidated at the group level.

---

## RECOMMENDATION

To complete NOTE 35: RELATED PARTY DISCLOSURES, please provide:
1. The **ttpl_impnotes.csv** file (Lifeline Diagnostics section) containing Related Party transaction and balance data
2. Or, a trial balance extract with the 'Ind AS Minor' column populated with the Related Party entity names and transaction types listed above

```json
{
  "note_number": "35",
  "note_title": "RELATED PARTY DISCLOSURES",
  "period": "Total June 2025",
  "data_status": "INCOMPLETE - NO RELATED PARTY ENTRIES FOUND IN SOURCE DATA",
  "excel_data": [
    {
      "particulars": "RELATED PARTY DISCLOSURES",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "(A) Names of related parties and related party relationship",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Related parties where control exists",
      "amount": 0,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Fellow Subsidiaries",
      "amount": 0,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Key Management Personnel ('KMP')",
      "amount": 0,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "(B) Transactions with related parties",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Transactions during the year (Management Fees, Rent, etc.)",
      "amount": 0,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "(C) Balances outstanding at year end",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Balances (Receivables, Payables, ROU Assets)",
      "amount": 0,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "TOTAL RELATED PARTY DISCLOSURES",
      "amount": 0,
      "is_bold": true,
      "is_total": true
    }
  ]
}
```

---

**Status:** Unable to generate complete NOTE 35 due to absence of Related Party transaction data in the provided trial balance. Please supply the supporting schedules/notes containing Related Party information.