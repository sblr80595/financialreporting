import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';
import type { CurrencyContext, CurrencyInfo } from '../types/currency';

interface CurrencySelectionContextType {
  currencyInfo: CurrencyInfo | null;
  fxRates: CurrencyContext['rates'];
  selectedCurrency: CurrencyInfo | null;
  setSelectedCurrencyCode: (code: string) => void;
  loading: boolean;
}

const CurrencySelectionContext = createContext<CurrencySelectionContextType | undefined>(undefined);

const STORAGE_KEY = (entity: string) => `currency:${entity}`;

export const CurrencySelectionProvider: React.FC<{ entity: string; children: React.ReactNode }> = ({
  entity,
  children,
}) => {
  const [selectedCode, setSelectedCode] = useState<string | null>(null);

  // Load persisted selection
  useEffect(() => {
    const persisted = entity ? localStorage.getItem(STORAGE_KEY(entity)) : null;
    if (persisted) setSelectedCode(persisted);
  }, [entity]);

  // Fetch currency context (local + FX)
  const { data: currencyContext, isLoading } = useQuery<CurrencyContext>(
    ['currency-context-shared', entity, selectedCode],
    async () => {
      const forceRefresh = !!selectedCode && selectedCode.length > 0;
      return await apiService.getCurrencyContext(entity, ['USD', 'INR'], forceRefresh);
    },
    {
      enabled: !!entity,
      staleTime: 0,
      refetchOnWindowFocus: false,
    }
  );

  const currencyInfo = currencyContext?.local_currency ?? null;
  const fxRates = currencyContext?.rates ?? [];

  // Derive effective currency (persist once local currency is known if not already set)
  useEffect(() => {
    if (!entity || !currencyInfo) return;
    if (!selectedCode) {
      setSelectedCode(currencyInfo.default_currency);
      localStorage.setItem(STORAGE_KEY(entity), currencyInfo.default_currency);
    }
  }, [currencyInfo, entity, selectedCode]);

  const selectedCurrency: CurrencyInfo | null = useMemo(() => {
    if (!currencyInfo) return null;
    const code = (selectedCode || currencyInfo.default_currency).toUpperCase();
    if (code === currencyInfo.default_currency.toUpperCase()) return currencyInfo;
    const known: Record<string, CurrencyInfo> = {
      USD: {
        entity_name: 'USD',
        default_currency: 'USD',
        currency_symbol: '$',
        currency_name: 'US Dollar',
        decimal_places: 2,
        format: '$ #,##0.00',
      },
      INR: {
        entity_name: 'INR',
        default_currency: 'INR',
        currency_symbol: '₹',
        currency_name: 'Indian Rupee',
        decimal_places: 2,
        format: '₹ #,##,##0.00',
      },
    };
    return known[code] ?? currencyInfo;
  }, [currencyInfo, selectedCode]);

  const setSelectedCurrencyCode = (code: string) => {
    setSelectedCode(code);
    if (entity) localStorage.setItem(STORAGE_KEY(entity), code);
  };

  return (
    <CurrencySelectionContext.Provider
      value={{
        currencyInfo,
        fxRates,
        selectedCurrency,
        setSelectedCurrencyCode,
        loading: isLoading,
      }}
    >
      {children}
    </CurrencySelectionContext.Provider>
  );
};

export const useCurrencySelection = () => {
  const ctx = useContext(CurrencySelectionContext);
  if (!ctx) throw new Error('useCurrencySelection must be used within CurrencySelectionProvider');
  return ctx;
};
