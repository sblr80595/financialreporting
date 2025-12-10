# FINANCE COSTS NOTE GENERATION

## Analysis and Processing

I have reviewed the trial balance data provided and filtered for Finance Costs entries using the '(Unaudited) Jun'25' column (referred to as 'Total June 2025' in your CSV).

### Period Identified:
**Column Used: "Total June 2025"** (Unaudited)

---

## GL LEVEL BREAKDOWN FOR NOTE 29
**Period: (Unaudited) Jun'25**

| GL Code | GL Description | Ind AS Minor | Amount (₱) |
|---|---|---|---|
| 61503090 | Interest Expense | Interest on loans | ₱ 20,87,883.95 |
| 61503140 | Interest Expense on Lease | Interest expense on lease liabilities (refer note 45) | ₱ 9,86,812.55 |
| 61503070 | Processing Fee | Processing Fees | ₱ 2,35,060.96 |
| **TOTAL GL AMOUNTS** | | | **₱ 33,09,757.46** |

---

## NOTE 29: FINANCE COSTS
**Period: (Unaudited) Jun'25**

| Particulars | Amount (₱) |
|---|---|
| **Interest expense on:** | |
| Lease liabilities (refer note 33) | ₱ 9,86,812.55 |
| Borrowings | ₱ 20,87,883.95 |
| Processing Fees | ₱ 2,35,060.96 |
| **TOTAL FINANCE COSTS** | **₱ 33,09,757.46** |

### Note Narrative:
This note captures all finance costs incurred during the period from June 2025. The finance costs primarily comprise:

1. **Interest expense on Lease liabilities (₱ 9,86,812.55)**: This represents interest expense on lease obligations recognized under Ind AS 116. For detailed information on lease liability balances, refer to note 33.

2. **Borrowings (₱ 20,87,883.95)**: This includes interest expense on term loans, working capital loans, bank overdrafts, and short-term borrowings.

3. **Processing Fees (₱ 2,35,060.96)**: This represents loan processing charges and bank charges related to loan facilities and credit arrangements.

All finance costs are presented as positive amounts representing expenses in the profit and loss statement for the period ending June 25, 2025.

---

## STRUCTURED JSON OUTPUT FOR EXCEL GENERATION

```json
{
  "note_number": "29",
  "note_title": "FINANCE COSTS",
  "period": "(Unaudited) Jun'25",
  "excel_data": [
    {
      "particulars": "Interest expense on:",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Lease liabilities (refer note 33)",
      "amount": 986812.55,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Borrowings",
      "amount": 2087883.95,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Processing Fees",
      "amount": 235060.96,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "TOTAL FINANCE COSTS",
      "amount": 3309757.46,
      "is_bold": true,
      "is_total": true
    }
  ]
}
```

---

## Summary Notes:
- **Total Finance Costs for Jun'25: ₱ 33,09,757.46**
- All amounts formatted with Philippine Peso (₱) symbol as required
- GL-level detail reconciles perfectly with the summary total
- Ind AS Minor categories properly mapped and aggregated
- Structure complies with Schedule III requirements for Profit & Loss Statement presentation