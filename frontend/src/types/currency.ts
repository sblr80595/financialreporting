export interface CurrencyInfo {
  entity_name: string;
  default_currency: string;
  currency_symbol: string;
  currency_name: string;
  decimal_places: number;
  format?: string;
}

export interface FxRate {
  base_currency: string;
  target_currency: string;
  rate: number;
  as_of: string;
  source: string;
}

export interface CurrencyContext {
  entity: string;
  local_currency: CurrencyInfo;
  reporting_currencies: string[];
  rates: FxRate[];
  last_refreshed: string;
}

export interface FxConversionResult {
  target_currency: string;
  converted_amount: number;
  rate: number;
  as_of: string;
  source: string;
}
