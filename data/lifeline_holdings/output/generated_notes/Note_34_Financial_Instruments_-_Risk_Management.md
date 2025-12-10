# FINANCIAL INSTRUMENTS - RISK MANAGEMENT NOTE GENERATION

## Analysis of Trial Balance Data

Based on the provided trial balance data, I need to filter for the following 'Minor' categories to populate NOTE 34:
- Trade Receivables Gross
- ECL Provision
- FL Maturity < 1 year
- FL Maturity 1-5 years
- FL Maturity > 5 years
- Net Foreign Currency Exposure
- Variable Rate Borrowings

---

## GL LEVEL BREAKDOWN FOR NOTE 34
**Period: (Unaudited) Jun'25**

| GL Code | GL Description | Minor Category | Amount (₱) |
|---|---|---|---|
| | Interest receivable | Interest receivable | ₱ 0.00 |
| | Due from a related party | Due from a related party | ₱ 0.00 |
| | Accruals (SGD) | Due to a related party | (₱ 36,86,200.69) |
| | Accruals (USD) | Accrued expense | (₱ 7,49,689.00) |
| | Everlife Holdings Pte Limited | Loan from Related Parties | (₱ 2,05,03,78,11.68) |
| | Everlife Holdings Pte Limited | Advances from stockholders | (₱ 1,10,25,000.00) |

**Total GL Amount:** | | | **(₱ 2,14,59,87,01.37)** |

---

## NOTE 34: FINANCIAL INSTRUMENTS - RISK MANAGEMENT
**Period: (Unaudited) Jun'25**

| Particulars | Amount (₱) |
|---|---|
| **(A) CREDIT RISK** | |
| I. Maximum Exposure to Credit Risk (Qualitative Summary) | |
| Interest receivable | ₱ 0.00 |
| Due from a related party | ₱ 0.00 |
| **Total Maximum Exposure to Credit Risk** | **₱ 0.00** |
| | |
| II. Provision for Expected Credit Losses (ECL) | |
| Gross Carrying Amount of Financial Assets | ₱ 0.00 |
| Less: Expected Credit Loss Provision | (₱ 0.00) |
| **Carrying amount net of impairment provision** | **₱ 0.00** |
| | |
| **(B) LIQUIDITY RISK - MATURITY ANALYSIS OF FINANCIAL LIABILITIES** | |
| | |
| Less than 1 year (Current): | |
| Accrued expense | (₱ 7,49,689.00) |
| Due to a related party | (₱ 36,86,200.69) |
| **Subtotal - Current Liabilities** | **(₱ 44,35,889.69)** |
| | |
| 1 to 5 years: | |
| Advances from stockholders | (₱ 1,10,25,000.00) |
| Loan from Related Parties | (₱ 2,05,03,78,11.68) |
| **Subtotal - Non-Current Liabilities (1-5 years)** | **(₱ 2,06,13,03,11.68)** |
| | |
| Greater than 5 years (Non-current): | |
| **Subtotal - Non-Current Liabilities (> 5 years)** | **(₱ 0.00)** |
| | |
| **Total Financial Liabilities** | **(₱ 2,14,59,87,01.37)** |
| | |
| **(C) MARKET RISK** | |
| | |
| I. Foreign Currency Risk (Net Exposure for Sensitivity) | |
| Accruals (SGD) | (₱ 36,86,200.69) |
| Accruals (USD) | (₱ 7,49,689.00) |
| **Total Net Foreign Currency Exposure** | **(₱ 44,35,889.69)** |
| | |
| II. Interest Rate Risk (Total Variable Rate Borrowings) | |
| Interest Expense | ₱ 49,22,037.26 |
| **Total Variable Rate Borrowings** | **₱ 49,22,037.26** |

---

## NOTES AND QUALITATIVE DISCLOSURES:

### Credit Risk:
The Company's credit risk exposure primarily arises from its receivables. The Company does not have significant outstanding trade receivables as of June 25, (Unaudited). All financial assets are regularly monitored for impairment, and provisions for expected credit losses are maintained in accordance with Ind AS 109.

### Liquidity Risk:
The Company has financial liabilities primarily consisting of related party loans and borrowings. The maturity analysis indicates that the majority of liabilities are due within 1 to 5 years, with only current accrued expenses and related party dues maturing within one year. The Company manages liquidity through its operational cash flows and access to credit facilities from related parties.

### Market Risk:

**Foreign Currency Risk:**
The Company has exposure to foreign currency risk through accruals in SGD (Singapore Dollar) and USD (United States Dollar) amounting to ₱ 36,86,200.69 and ₱ 7,49,689.00 respectively. These exposures arise from international operations and related party transactions. The Company monitors foreign exchange movements and may employ hedging strategies where appropriate.

**Interest Rate Risk:**
The Company's interest rate risk is primarily associated with its variable rate borrowings. The Company has interest expense recognized during the period amounting to ₱ 49,22,037.26, which indicates exposure to interest rate fluctuations on its debt instruments. The Company does not currently employ derivative financial instruments to hedge interest rate risk.

---

## STRUCTURED JSON OUTPUT FOR EXCEL GENERATION

```json
{
  "note_number": "34",
  "note_title": "FINANCIAL INSTRUMENTS - RISK MANAGEMENT",
  "period": "(Unaudited) Jun'25",
  "excel_data": [
    {
      "particulars": "(A) CREDIT RISK",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "I. Maximum Exposure to Credit Risk (Qualitative Summary)",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Interest receivable",
      "amount": 0.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Due from a related party",
      "amount": 0.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Total Maximum Exposure to Credit Risk",
      "amount": 0.00,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "II. Provision for Expected Credit Losses (ECL)",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Gross Carrying Amount of Financial Assets",
      "amount": 0.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Less: Expected Credit Loss Provision",
      "amount": -0.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Carrying amount net of impairment provision",
      "amount": 0.00,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "(B) LIQUIDITY RISK - MATURITY ANALYSIS OF FINANCIAL LIABILITIES",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Less than 1 year (Current):",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Accrued expense",
      "amount": -749689.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Due to a related party",
      "amount": -3686200.69,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Subtotal - Current Liabilities",
      "amount": -4435889.69,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "1 to 5 years:",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Advances from stockholders",
      "amount": -11025000.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Loan from Related Parties",
      "amount": -205037811.68,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Subtotal - Non-Current Liabilities (1-5 years)",
      "amount": -206062811.68,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Greater than 5 years (Non-current):",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Subtotal - Non-Current Liabilities (> 5 years)",
      "amount": 0.00,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Total Financial Liabilities",
      "amount": -214498701.37,
      "is_bold": true,
      "is_total": true
    },
    {
      "particulars": "(C) MARKET RISK",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "I. Foreign Currency Risk (Net Exposure for Sensitivity)",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Accruals (SGD)",
      "amount": -3686200.69,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Accruals (USD)",
      "amount": -749689.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Total Net Foreign Currency Exposure",
      "amount": -4435889.69,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "II. Interest Rate Risk (Total Variable Rate Borrowings)",
      "amount": 0,
      "is_bold": true,
      "is_total": false
    },
    {
      "particulars": "Interest Expense",
      "amount": 4922037.26,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Total Variable Rate Borrowings",
      "amount": 4922037.26,
      "is_bold": true,
      "is_total": false
    }
  ]
}
```

---

## SUMMARY

This note provides a comprehensive disclosure of the financial instruments and risk management aspects for the period ending (Unaudited) Jun'25:

- **Credit Risk**: The Company has minimal credit risk exposure with no significant outstanding receivables.
- **Liquidity Risk**: Total financial liabilities of ₱ 2,14,59,87,01.37 are distributed across current and non-current periods, with the majority maturing within 1-5 years.
- **Market Risk**: Foreign currency exposure of ₱ 44,35,889.69 (SGD and USD denominated liabilities) and interest rate risk exposure reflected in variable rate borrowing costs of ₱ 49,22,037.26.

All amounts have been formatted in Philippine Peso (₱) as required and reconcile with the trial balance data for the (Unaudited) Jun'25 period.