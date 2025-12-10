# FINANCIAL NOTE GENERATION
## NOTE 9: TRADE RECEIVABLES

---

### GL LEVEL BREAKDOWN FOR NOTE 9
**Period: (Unaudited) Jun'25**

| GL Code | GL Description | Amount (₹) |
|---------|----------------|------------|
| **Trade receivables- Unsecured, considered good** | | |
| 200111 | Trade Debtors (Domestic) | 22,807.43 |
| 200112 | Trade Debtors (Export) | 718.44 |
| 200113 | Debtors - RR | (3.99) |
| 200114 | Non- Recognised Receipt | 1.23 |
| 200123 | Trade Debtors Related Parties Domestic | (191.99) |
| 200124 | Trade Debtors Related Parties Import | 1,734.59 |
| 200125 | Debtors for JV | 0.00 |
| **Subtotal - Unsecured, considered good** | | **₹25,065.71** |
| | | |
| **Allowance for bad and doubtful debts** | | |
| 200121 | Sundry Debtors (Doubtful) | (347.67) |
| **Subtotal - Allowance** | | **₹(347.67)** |
| | | |
| **Total from GLs** | | **₹24,718.04** |

---

### NOTE 9: TRADE RECEIVABLES
**Period: (Unaudited) Jun'25**

| Particulars | Amount (₹) |
|-------------|------------|
| **Trade receivables** | |
| Unsecured, considered good | ₹25,065.71 |
| Unsecured, considered impaired | ₹347.67 |
| **SUBTOTAL_TRADE_RECEIVABLES (Gross)** | **₹25,413.38** |
| | |
| **Impairment allowance** | |
| Less: Provision for doubtful debts | (₹347.67) |
| | |
| **TOTAL_TRADE_RECEIVABLES (Net)** | **₹25,065.71** |

---

### NOTES AND EXPLANATIONS:

1. **Trade receivables - Unsecured, considered good**: This represents the sum of all trade receivables that are considered recoverable, totaling ₹25,065.71 lakhs.

2. **Unsecured, considered impaired**: This represents the gross amount of trade receivables that are considered doubtful and have been provided for. The amount of ₹347.67 lakhs is derived from the 'Allowance for bad and doubtful debts' account (GL Code 200121), with the sign flipped to show the gross receivable amount before impairment.

3. **Gross Trade Receivables**: The total of 'considered good' and 'considered impaired' gives us the gross trade receivables of ₹25,413.38 lakhs.

4. **Impairment Allowance**: The provision for doubtful debts of ₹347.67 lakhs (same amount as impaired receivables) is deducted to arrive at the net realizable value.

5. **Net Trade Receivables**: After deducting the impairment allowance, the net trade receivables amount to ₹25,065.71 lakhs, which represents the carrying value of trade receivables in the balance sheet.

6. **Reconciliation**: Net Trade Receivables (₹25,065.71) = Gross Trade Receivables (₹25,413.38) - Impairment Allowance (₹347.67)

---

## STRUCTURED JSON OUTPUT FOR EXCEL GENERATION

```json
{
  "note_number": "9",
  "note_title": "TRADE RECEIVABLES",
  "period": "(Unaudited) Jun'25",
  "excel_data": [
    {
      "particulars": "Trade receivables",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Unsecured, considered good",
      "amount": 25065.71,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Unsecured, considered impaired",
      "amount": 347.67,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "SUBTOTAL_TRADE_RECEIVABLES (Gross)",
      "amount": 25413.38,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Impairment allowance",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Less: Provision for doubtful debts",
      "amount": -347.67,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "TOTAL_TRADE_RECEIVABLES (Net)",
      "amount": 25065.71,
      "is_bold": true,
      "is_total": true
    }
  ]
}
```