# NOTE 30: DEPRECIATION AND AMORTISATION EXPENSE

## Analysis of Trial Balance Data

I have carefully reviewed the provided trial balance CSV data for the period **(Unaudited) Jun'25**.

### Finding:

After filtering the trial balance by the 'Minor' column (which corresponds to 'Ind AS Minor' in standard accounting classifications) for the following categories:
- "Dep. On PPE" (Depreciation on Property, Plant & Equipment)
- "Dep. On ROU" (Depreciation on Right of Use Assets)
- "Amortisation of intangible assets (refer note 5A)"

**Result: NO entries found** matching these depreciation and amortisation categories in the trial balance for the period (Unaudited) Jun'25.

---

## GL Level Breakdown for NOTE 30
**Period: (Unaudited) Jun'25**

| GL Code | GL Description | Amount (₱) |
|---|---|---|
| **No matching GL entries found** | — | — |
| **Total:** | | **₱ 0.00** |

---

## NOTE 30: DEPRECIATION AND AMORTISATION EXPENSE
**Period: (Unaudited) Jun'25**

| Particulars | Amount (₱) |
|---|---|
| Depreciation on property, plant and equipment (refer note 4) | ₱ 0.00 |
| Depreciation on right of use assets (refer note 4A) | ₱ 0.00 |
| Amortisation of intangible assets (refer note 4B) | ₱ 0.00 |
| **TOTAL DEPRECIATION AND AMORTISATION EXPENSE** | **₱ 0.00** |

---

## Notes:
1. The trial balance provided does not contain any GL accounts categorized under depreciation or amortisation expense for the period (Unaudited) Jun'25.
2. This suggests that either:
   - No depreciable or amortisable assets were held during this period, or
   - Depreciation/amortisation GL accounts are recorded under different line item descriptions not matching the specified categories.
3. If depreciation and amortisation expenses should be present, please verify the trial balance data and GL account classifications.

---

## STRUCTURED OUTPUT FOR EXCEL GENERATION

```json
{
  "note_number": "30",
  "note_title": "DEPRECIATION AND AMORTISATION EXPENSE",
  "period": "(Unaudited) Jun'25",
  "excel_data": [
    {
      "particulars": "Depreciation on property, plant and equipment (refer note 4)",
      "amount": 0.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Depreciation on right of use assets (refer note 4A)",
      "amount": 0.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "Amortisation of intangible assets (refer note 4B)",
      "amount": 0.00,
      "is_bold": false,
      "is_total": false
    },
    {
      "particulars": "TOTAL DEPRECIATION AND AMORTISATION EXPENSE",
      "amount": 0.00,
      "is_bold": true,
      "is_total": true
    }
  ]
}
```