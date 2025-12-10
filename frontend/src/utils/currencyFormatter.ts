/**
 * Currency Formatting Utility
 *
 * Implements comprehensive currency formatting guidelines:
 * - Currency Symbol: Placed before the number with a space (e.g., € 1.234,56)
 * - Thousands Separator: Indian grouping for INR; comma for others
 * - Decimal Separator: Period for all
 * - Negative Numbers: Displayed in parentheses (e.g., ($ 1,234.56))
 */

import { CurrencyInfo } from '../types/currency';

export interface CurrencyFormatOptions {
  showDecimals?: boolean;
  decimalPlaces?: number;
}

/**
 * Format a number as currency with proper symbols and separators
 * 
 * @param value - The numeric value to format
 * @param currencyInfo - Currency information for the entity
 * @param options - Optional formatting options
 * @returns Formatted currency string
 * 
 * @example
 * formatCurrency(1234.56, currencyInfo) // "€ 1.234,56"
 * formatCurrency(-1234.56, currencyInfo) // "(€ 1.234,56)"
 * formatCurrency(1234567.89, currencyInfo) // "€ 1.234.567,89"
 */
export function formatCurrency(
  value: number,
  currencyInfo: CurrencyInfo | null | undefined,
  options: CurrencyFormatOptions = {}
): string {
  const {
    showDecimals = true,
    decimalPlaces = currencyInfo?.decimal_places ?? 2,
  } = options;

  // Default to INR if no currency info provided
  if (!currencyInfo) {
    const isNegative = value < 0;
    const absValue = Math.abs(value);
    const formatted = new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: showDecimals ? decimalPlaces : 0,
      maximumFractionDigits: showDecimals ? decimalPlaces : 0,
    }).format(absValue);
    const result = `₹ ${formatted}`;
    return isNegative ? `(${result})` : result;
  }

  const isNegative = value < 0;
  const absValue = Math.abs(value);
  
  const locale = currencyInfo.default_currency === 'INR' ? 'en-IN' : 'en-US';

  const formatted = new Intl.NumberFormat(locale, {
    minimumFractionDigits: showDecimals ? decimalPlaces : 0,
    maximumFractionDigits: showDecimals ? decimalPlaces : 0,
  }).format(absValue);

  // Format with currency symbol before the number with a space
  const result = `${currencyInfo.currency_symbol} ${formatted}`;
  
  // For negative numbers, wrap in parentheses
  return isNegative ? `(${result})` : result;
}

/**
 * Format currency without decimals
 * 
 * @param value - The numeric value to format
 * @param currencyInfo - Currency information for the entity
 * @returns Formatted currency string without decimals
 * 
 * @example
 * formatCurrencyWhole(1234.56, currencyInfo) // "$ 1,235"
 */
export function formatCurrencyWhole(
  value: number,
  currencyInfo: CurrencyInfo | null | undefined
): string {
  return formatCurrency(value, currencyInfo, { showDecimals: false, decimalPlaces: 0 });
}

/**
 * Format a compact currency value (for large numbers)
 * 
 * @param value - The numeric value to format
 * @param currencyInfo - Currency information for the entity
 * @returns Compact formatted currency string
 * 
 * @example
 * formatCurrencyCompact(1234567, currencyInfo) // "$ 1.23M"
 * formatCurrencyCompact(1234, currencyInfo) // "$ 1.23K"
 */
export function formatCurrencyCompact(
  value: number,
  currencyInfo: CurrencyInfo | null | undefined
): string {
  const isNegative = value < 0;
  const absValue = Math.abs(value);
  
  const symbol = currencyInfo?.currency_symbol || '₹';
  const useIndian = currencyInfo?.default_currency === 'INR';

  const formatNumber = (num: number) =>
    new Intl.NumberFormat(useIndian ? 'en-IN' : 'en-US', {
      maximumFractionDigits: 2,
    }).format(num);

  let formatted: string;
  if (absValue >= 1_000_000_000) {
    formatted = `${symbol} ${formatNumber(absValue / 1_000_000_000)}B`;
  } else if (absValue >= 1_000_000) {
    formatted = `${symbol} ${formatNumber(absValue / 1_000_000)}M`;
  } else if (absValue >= 1_000) {
    formatted = `${symbol} ${formatNumber(absValue / 1_000)}K`;
  } else {
    formatted = formatCurrency(absValue, currencyInfo);
  }
  
  return isNegative ? `(${formatted})` : formatted;
}

/**
 * Parse a formatted currency string back to a number
 * 
 * @param currencyString - The formatted currency string
 * @returns Numeric value
 * 
 * @example
 * parseCurrency("$ 1,234.56") // 1234.56
 * parseCurrency("($ 1,234.56)") // -1234.56
 */
export function parseCurrency(currencyString: string): number {
  // Check if negative (in parentheses)
  const isNegative = currencyString.trim().startsWith('(') && currencyString.trim().endsWith(')');

  // Strip currency symbols and whitespace
  let cleaned = currencyString.replace(/[()$€¥₹₱RMS$]/g, '').trim();
  cleaned = cleaned.replace(/\s+/g, '');

  // Assume comma thousands, dot decimal for non-INR; Indian uses comma thousands as well.
  // Normalize by removing commas and keeping dot as decimal separator.
  cleaned = cleaned.replace(/,/g, '');

  const value = parseFloat(cleaned);

  return isNegative ? -value : value;
}
