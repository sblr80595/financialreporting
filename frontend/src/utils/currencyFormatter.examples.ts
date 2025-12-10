/**
 * Currency Formatting Examples and Tests
 * 
 * This file demonstrates the comprehensive currency formatting implementation
 * across different currencies and scenarios.
 */

import { formatCurrency } from './currencyFormatter';
import type { CurrencyInfo } from '../types/currency';

// Example currency configurations
const currencies: Record<string, CurrencyInfo> = {
  PHP: {
    entity_name: "Lifeline Holdings",
    default_currency: "PHP",
    currency_symbol: "₱",
    currency_name: "Philippine Peso",
    decimal_places: 2,
    format: "₱ #,##0.00"
  },
  USD: {
    entity_name: "Integris",
    default_currency: "USD",
    currency_symbol: "$",
    currency_name: "US Dollar",
    decimal_places: 2,
    format: "$ #,##0.00"
  },
  INR: {
    entity_name: "Analisa Resource",
    default_currency: "INR",
    currency_symbol: "₹",
    currency_name: "Indian Rupee",
    decimal_places: 2,
    format: "₹ #,##,##0.00"
  },
  EUR: {
    entity_name: "Hausen",
    default_currency: "EUR",
    currency_symbol: "€",
    currency_name: "Euro",
    decimal_places: 2,
    format: "€ #,##0.00"
  },
  MYR: {
    entity_name: "CPM Malaysia",
    default_currency: "MYR",
    currency_symbol: "RM",
    currency_name: "Malaysian Ringgit",
    decimal_places: 2,
    format: "RM #,##0.00"
  }
};

/**
 * Test Examples - Expected Output Format:
 * 
 * Positive Numbers:
 * ----------------
 * formatCurrency(1234.56, currencies.USD)    => "$ 1,234.56"
 * formatCurrency(1234567.89, currencies.USD) => "$ 1,234,567.89"
 * formatCurrency(1000000, currencies.PHP)    => "₱ 1,000,000.00"
 * formatCurrency(15533159, currencies.INR)   => "₹ 1,55,33,159.00" (Indian numbering)
 * formatCurrency(10000, currencies.EUR)      => "€ 10,000.00"
 * formatCurrency(25000, currencies.MYR)      => "RM 25,000.00"
 * 
 * Negative Numbers (in parentheses):
 * ----------------------------------
 * formatCurrency(-1234.56, currencies.USD)     => "($ 1,234.56)"
 * formatCurrency(-1142840, currencies.PHP)     => "(₱ 1,142,840.00)"
 * formatCurrency(-172689, currencies.INR)      => "(₹ 1,72,689.00)"
 * formatCurrency(-50000.75, currencies.EUR)    => "(€ 50,000.75)"
 * formatCurrency(-1800, currencies.INR)        => "(₹ 1,800.00)"
 * 
 * Zero Values:
 * -----------
 * formatCurrency(0, currencies.USD)            => "$ 0.00"
 * formatCurrency(0, currencies.PHP)            => "₱ 0.00"
 * 
 * Key Formatting Rules Applied:
 * ----------------------------
 * 1. Currency Symbol: Always placed BEFORE the number with a SPACE
 *    - Correct: "$ 1,234.56"
 *    - Incorrect: "$1,234.56" or "1,234.56 $"
 * 
 * 2. Thousands Separator: COMMA (,)
 *    - Standard format: 1,234,567.89
 *    - Indian format: 1,55,33,159.00 (lakhs and crores system)
 * 
 * 3. Decimal Separator: PERIOD (.)
 *    - Always use period for decimal separation
 *    - Always show 2 decimal places
 * 
 * 4. Negative Numbers: Wrapped in PARENTHESES
 *    - Correct: "($ 1,234.56)"
 *    - Incorrect: "-$ 1,234.56" or "$ -1,234.56"
 * 
 * 5. Decimal Precision: Always 2 decimal places
 *    - Even for whole numbers: "$ 1,000.00" (not "$ 1,000")
 * 
 * Usage in Components:
 * -------------------
 * ```tsx
 * import { formatCurrency } from '../utils/currencyFormatter';
 * import { useQuery } from 'react-query';
 * import { apiService } from '../services/api';
 * 
 * function MyComponent() {
 *   const { selectedEntity } = useEntity();
 *   
 *   // Fetch currency info for selected entity
 *   const { data: currencyInfo } = useQuery(
 *     ['entity-currency', selectedEntity],
 *     () => apiService.getCompanyCurrency(selectedEntity)
 *   );
 *   
 *   // Use in rendering
 *   return (
 *     <div>
 *       <p>Total: {formatCurrency(1234567.89, currencyInfo)}</p>
 *       <p>Debit: {formatCurrency(15533159, currencyInfo)}</p>
 *       <p>Credit: {formatCurrency(-408076, currencyInfo)}</p>
 *     </div>
 *   );
 * }
 * ```
 */

// Console test examples (uncomment to test)
/*
console.log('=== Positive Numbers ===');
console.log('USD:', formatCurrency(1234.56, currencies.USD));
console.log('PHP:', formatCurrency(1142840, currencies.PHP));
console.log('INR:', formatCurrency(15533159, currencies.INR));
console.log('EUR:', formatCurrency(10000, currencies.EUR));
console.log('MYR:', formatCurrency(25000, currencies.MYR));

console.log('\n=== Negative Numbers ===');
console.log('USD:', formatCurrency(-1234.56, currencies.USD));
console.log('PHP:', formatCurrency(-1142840, currencies.PHP));
console.log('INR:', formatCurrency(-172689, currencies.INR));
console.log('EUR:', formatCurrency(-50000.75, currencies.EUR));
console.log('INR:', formatCurrency(-1800, currencies.INR));

console.log('\n=== Zero Values ===');
console.log('USD:', formatCurrency(0, currencies.USD));
console.log('PHP:', formatCurrency(0, currencies.PHP));
*/

export { };
