// src/pages/FinAnalyzerReportsPage.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { DocumentTextIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { useEntity } from '../contexts/EntityContext';
import FinAnalyzerCategorySelection from './FinAnalyzerCategorySelection';
import toast from 'react-hot-toast';
import { 
  finAnalyzerPNLApi, 
  finAnalyzerPNLScheduleApi, 
  cashFlowFinalizerApi,
  bsFinalizerApi,         
  bsScheduleApi,         
  equityScheduleApi,      
  StatementReadinessResponse,
  CashFlowFinalizerReadinessResponse,
  apiService
} from '../services/api';
import { CurrencyContext, CurrencyInfo } from '../types/currency';

interface FinAnalyzerCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
}

const FinAnalyzerReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();
  const companyName = getCompanyName();
  const [selectedCurrencyCode, setSelectedCurrencyCode] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<FinAnalyzerCategory | null>(null);
  const [loading, setLoading] = useState(false);
  const [readiness, setReadiness] = useState<StatementReadinessResponse | CashFlowFinalizerReadinessResponse | null>(null);
  const [checkingReadiness, setCheckingReadiness] = useState(false);
  const { data: currencyContext, refetch: refetchCurrencyContext } = useQuery<CurrencyContext>(
    ['currency-context', companyName, selectedCurrencyCode],
    () => {
      const forceRefresh =
        !!selectedCurrencyCode &&
        localCurrency &&
        selectedCurrencyCode !== localCurrency.default_currency;
      return apiService.getCurrencyContext(companyName, ['USD', 'INR'], forceRefresh);
    },
    { enabled: !!companyName, staleTime: 0, refetchOnWindowFocus: false }
  );
  const localCurrency: CurrencyInfo | undefined = currencyContext?.local_currency;
  const fxRates = currencyContext?.rates || [];

  useEffect(() => {
    if (localCurrency && !selectedCurrencyCode) {
      setSelectedCurrencyCode(localCurrency.default_currency);
    }
  }, [localCurrency, selectedCurrencyCode]);

  useEffect(() => {
    if (
      selectedCurrencyCode &&
      localCurrency &&
      selectedCurrencyCode !== localCurrency.default_currency
    ) {
      refetchCurrencyContext();
    }
  }, [selectedCurrencyCode, localCurrency, refetchCurrencyContext]);

  const getCurrencyInfoForCode = (code?: string | null): CurrencyInfo | undefined => {
    if (!code) return localCurrency;
    const upper = code.toUpperCase();
    if (upper === localCurrency?.default_currency?.toUpperCase()) return localCurrency;
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
      EUR: {
        entity_name: 'EUR',
        default_currency: 'EUR',
        currency_symbol: '€',
        currency_name: 'Euro',
        decimal_places: 2,
        format: '€ #,##0.00',
      },
      MYR: {
        entity_name: 'MYR',
        default_currency: 'MYR',
        currency_symbol: 'RM',
        currency_name: 'Malaysian Ringgit',
        decimal_places: 2,
        format: 'RM #,##0.00',
      },
    };
    return known[upper];
  };

  const selectedCurrency = getCurrencyInfoForCode(selectedCurrencyCode || undefined) || localCurrency;
  const currencyName = selectedCurrency?.currency_name || 'Malaysian Ringgit';
  const currencyPrefix = selectedCurrency?.currency_symbol || 'RM';
  const currencyContextCard = localCurrency ? (
    <div className="card">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <p className="text-sm text-gray-500">Local currency</p>
          <p className="text-lg font-semibold text-gray-900">
            {localCurrency.currency_symbol} ({localCurrency.default_currency}) — {localCurrency.currency_name}
          </p>
          <p className="text-xs text-gray-500">Entity: {localCurrency.entity_name}</p>
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-gray-600">View as:</span>
            <div className="inline-flex rounded-md shadow-sm overflow-hidden border border-gray-200">
              {[localCurrency.default_currency, 'USD', 'INR'].map((code) => (
                <button
                  key={code}
                  onClick={() => setSelectedCurrencyCode(code)}
                  className={`px-3 py-1 text-sm ${
                    selectedCurrencyCode === code
                      ? 'bg-primary-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50'
                  } border-r border-gray-200 last:border-0`}
                >
                  {code}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="sm:text-right">
          <p className="text-sm text-gray-500">Reporting (USD / INR)</p>
          <div className="flex flex-wrap gap-2 mt-1 justify-end">
            {fxRates.length ? fxRates.map((rate) => (
              <div
                key={`${rate.base_currency}-${rate.target_currency}`}
                className="inline-flex items-center border border-gray-200 rounded-md px-3 py-1 bg-gray-50"
              >
                <span className="text-xs text-gray-600">1 {rate.base_currency}</span>
                <span className="mx-1 text-gray-400">→</span>
                <span className="text-sm font-semibold text-gray-800">
                  {new Intl.NumberFormat('en-US', { maximumFractionDigits: 4 }).format(rate.rate)} {rate.target_currency}
                </span>
                <span className="ml-2 text-[11px] text-gray-500">{rate.source}</span>
              </div>
            )) : (
              <span className="text-xs text-gray-500">FX rates unavailable. Using cached/local currency.</span>
            )}
          </div>
          {currencyContext?.last_refreshed && (
            <p className="text-[11px] text-gray-500 mt-1">
              Updated {new Date(currencyContext.last_refreshed).toLocaleString()}
            </p>
          )}
        </div>
      </div>
    </div>
  ) : null;

  // Define the 6 FinAnalyzer report categories

const categories: FinAnalyzerCategory[] = [
  {
    id: 'finanalyzer-pl',
    name: 'FinAnalyzer P&L',
    icon: '💰',
    description: 'Comprehensive Profit & Loss statement analysis'
  },
  {
    id: 'finanalyzer-pl-schedule',
    name: 'FinAnalyzer P&L Schedule',
    icon: '📋',
    description: 'Detailed P&L schedules and breakdowns'
  },
  {
    id: 'finanalyzer-bs',
    name: 'FinAnalyzer Balance Sheet',
    icon: '📊',
    description: 'Complete Balance Sheet analysis'
  },
  {
    id: 'finanalyzer-bs-schedule',
    name: 'FinAnalyzer BS Schedule',
    icon: '📑',
    description: 'Detailed Balance Sheet schedules'
  },
  {
    id: 'finanalyzer-cashflow',
    name: 'FinAnalyzer Cash Flow',
    icon: '💵',
    description: 'Cash flow statement and analysis'
  },
  {
    id: 'finanalyzer-equity',
    name: 'FinAnalyzer Equity',
    icon: '🏦',
    description: 'Statement of changes in equity'
  }
];




const handleGenerateBSFinalyzer = async () => {
  const bsReadiness = readiness as StatementReadinessResponse;
  if (!bsReadiness?.is_ready) {
    toast.error('Please ensure all required notes are generated first');
    return;
  }

  setLoading(true);
  try {
    toast.loading('Generating BS Finalyzer...', { id: 'generating' });
    
    const result = await bsFinalizerApi.generateBSFinalyzer({
      company_name: companyName,
      period_label: '2025 Mar YTD',
      entity_info: 'Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual',
      currency: currencyName,
      scenario: 'Actual'
    });

    toast.dismiss('generating');
    
    if (result.success) {
      toast.success('BS Finalyzer generated successfully!');
      await bsFinalizerApi.triggerBSFinalizerDownload(companyName);
    } else {
      toast.error(result.message || 'Failed to generate BS Finalyzer');
    }
  } catch (err: any) {
    toast.dismiss('generating');
    console.error('Error generating BS Finalyzer:', err);
    toast.error(err.response?.data?.detail || 'Failed to generate BS Finalyzer');
  } finally {
    setLoading(false);
  }
};

const handleGenerateBSSchedule = async () => {
  const bsReadiness = readiness as StatementReadinessResponse;
  if (!bsReadiness?.is_ready) {
    toast.error('Please ensure all required notes are generated first');
    return;
  }

  setLoading(true);
  try {
    toast.loading('Generating BS Schedule...', { id: 'generating' });
    
    const result = await bsScheduleApi.generateBSSchedule({
      company_name: companyName,
      period_label: '2025 Mar YTD',
      entity_info: 'Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual',
      currency: currencyName,
      scenario: 'Actual',
      show_currency_prefix: true,
      currency_prefix: currencyPrefix,
      convert_to_lakh: true
    });

    toast.dismiss('generating');
    
    if (result.success) {
      toast.success('BS Schedule generated successfully!');
      await bsScheduleApi.triggerBSScheduleDownload(companyName);
    } else {
      toast.error(result.message || 'Failed to generate BS Schedule');
    }
  } catch (err: any) {
    toast.dismiss('generating');
    console.error('Error generating BS Schedule:', err);
    toast.error(err.response?.data?.detail || 'Failed to generate BS Schedule');
  } finally {
    setLoading(false);
  }
};

const handleGenerateEquitySchedule = async () => {
  const equityReadiness = readiness as StatementReadinessResponse;
  if (!equityReadiness?.is_ready) {
    toast.error('Please ensure all required notes are generated first');
    return;
  }

  setLoading(true);
  try {
    toast.loading('Generating Equity Schedule...', { id: 'generating' });
    
    const result = await equityScheduleApi.generateEquitySchedule({
      company_name: companyName,
      period_label: '2025 Mar YTD',
      entity_info: 'Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual',
      currency: currencyName,
      scenario: 'Actual',
      show_currency_prefix: true,
      currency_prefix: currencyPrefix,
      convert_to_lakh: false
    });

    toast.dismiss('generating');
    
    if (result.success) {
      toast.success('Equity Schedule generated successfully!');
      await equityScheduleApi.triggerEquityScheduleDownload(companyName);
    } else {
      toast.error(result.message || 'Failed to generate Equity Schedule');
    }
  } catch (err: any) {
    toast.dismiss('generating');
    console.error('Error generating Equity Schedule:', err);
    toast.error(err.response?.data?.detail || 'Failed to generate Equity Schedule');
  } finally {
    setLoading(false);
  }
};

  const checkPNLReadiness = useCallback(async () => {
    setCheckingReadiness(true);
    try {
      const result = await finAnalyzerPNLApi.checkReadiness(companyName);
      setReadiness(result);
      
      if (!result.is_ready) {
        toast.error(
          `Missing notes: ${result.missing_notes.join(', ')}. Please generate all required notes first.`,
          { duration: 5000 }
        );
      }
    } catch (err) {
      console.error('Error checking readiness:', err);
      toast.error('Failed to check report readiness');
    } finally {
      setCheckingReadiness(false);
    }
  }, [companyName]);

  const checkPNLScheduleReadiness = useCallback(async () => {
    setCheckingReadiness(true);
    try {
      const result = await finAnalyzerPNLScheduleApi.checkReadiness(companyName);
      setReadiness(result);
      
      if (!result.is_ready) {
        toast.error(
          `Missing notes: ${result.missing_notes.join(', ')}. Please generate all required notes first.`,
          { duration: 5000 }
        );
      }
    } catch (err) {
      console.error('Error checking readiness:', err);
      toast.error('Failed to check report readiness');
    } finally {
      setCheckingReadiness(false);
    }
  }, [companyName]);

  const checkCashFlowReadiness = useCallback(async () => {
    setCheckingReadiness(true);
    try {
      const result = await cashFlowFinalizerApi.checkReadiness(companyName);
      setReadiness(result);
      
      if (!result.is_ready) {
        toast.error(result.message, { duration: 5000 });
      }
    } catch (err) {
      console.error('Error checking Cash Flow readiness:', err);
      toast.error('Failed to check Cash Flow readiness');
    } finally {
      setCheckingReadiness(false);
    }
  }, [companyName]);

  const handleSelectCategory = (category: FinAnalyzerCategory) => {
    setSelectedCategory(category);
    setReadiness(null); // Reset readiness when changing category
  };

  const handleBackToCategories = () => {
    setSelectedCategory(null);
    setReadiness(null);
  };

  const checkBSFinalizerReadiness = useCallback(async () => {
    setCheckingReadiness(true);
    try {
      const result = await bsFinalizerApi.checkReadiness(companyName);
      setReadiness(result);
      
      if (!result.is_ready) {
        toast.error(
          `Missing notes: ${result.missing_notes.join(', ')}. Please generate all required notes first.`,
          { duration: 5000 }
        );
      }
    } catch (err) {
      console.error('Error checking BS Finalyzer readiness:', err);
      toast.error('Failed to check BS Finalyzer readiness');
    } finally {
      setCheckingReadiness(false);
    }
  }, [companyName]);

const checkBSScheduleReadiness = useCallback(async () => {
  setCheckingReadiness(true);
  try {
    const result = await bsScheduleApi.checkReadiness(companyName);
    setReadiness(result);
    
    if (!result.is_ready) {
      toast.error(
        `Missing notes: ${result.missing_notes.join(', ')}. Please generate all required notes first.`,
        { duration: 5000 }
      );
    }
  } catch (err) {
    console.error('Error checking BS Schedule readiness:', err);
    toast.error('Failed to check BS Schedule readiness');
  } finally {
    setCheckingReadiness(false);
  }
}, [companyName]);

const checkEquityScheduleReadiness = useCallback(async () => {
  setCheckingReadiness(true);
  try {
    const result = await equityScheduleApi.checkReadiness(companyName);
    setReadiness(result);
    
    if (!result.is_ready) {
      toast.error(
        `Missing notes: ${result.missing_notes.join(', ')}. Please generate all required notes first.`,
        { duration: 5000 }
      );
    }
  } catch (err) {
    console.error('Error checking Equity Schedule readiness:', err);
    toast.error('Failed to check Equity Schedule readiness');
  } finally {
    setCheckingReadiness(false);
  }
}, [companyName]);

  // Check readiness when category is selected — callbacks are memoized above
  useEffect(() => {
    if (selectedCategory?.id === 'finanalyzer-pl') {
      checkPNLReadiness();
    } else if (selectedCategory?.id === 'finanalyzer-pl-schedule') {
      checkPNLScheduleReadiness();
    } else if (selectedCategory?.id === 'finanalyzer-cashflow') {
      checkCashFlowReadiness();
    } else if (selectedCategory?.id === 'finanalyzer-bs') {
      checkBSFinalizerReadiness();
    } else if (selectedCategory?.id === 'finanalyzer-bs-schedule') {
      checkBSScheduleReadiness();
    } else if (selectedCategory?.id === 'finanalyzer-equity') {
      checkEquityScheduleReadiness();
    }
  }, [
    selectedCategory,
    checkPNLReadiness,
    checkPNLScheduleReadiness,
    checkCashFlowReadiness,
    checkBSFinalizerReadiness,
    checkBSScheduleReadiness,
    checkEquityScheduleReadiness,
  ]);

  const handleGeneratePNLFinalyzer = async () => {
    const pnlReadiness = readiness as StatementReadinessResponse;
    if (!pnlReadiness?.is_ready) {
      toast.error('Please ensure all required notes are generated first');
      return;
    }

    setLoading(true);
    try {
      toast.loading('Generating PNL Finalyzer...', { id: 'generating' });
      
    const result = await finAnalyzerPNLApi.generatePNLFinalyzer({
      company_name: companyName,
      period_label: '2025 Mar YTD',
      entity_info: 'Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual',
      currency: currencyName,
      scenario: 'Actual'
    });

      toast.dismiss('generating');
      
      if (result.success) {
        toast.success('PNL Finalyzer generated successfully!');
        await finAnalyzerPNLApi.triggerPNLFinalyzerDownload(companyName);
      } else {
        toast.error(result.message || 'Failed to generate PNL Finalyzer');
      }
    } catch (err: any) {
      toast.dismiss('generating');
      console.error('Error generating PNL Finalyzer:', err);
      toast.error(err.response?.data?.detail || 'Failed to generate PNL Finalyzer');
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePNLSchedule = async () => {
    const pnlReadiness = readiness as StatementReadinessResponse;
    if (!pnlReadiness?.is_ready) {
      toast.error('Please ensure all required notes are generated first');
      return;
    }

    setLoading(true);
    try {
      toast.loading('Generating PNL Schedule...', { id: 'generating' });
      
    const result = await finAnalyzerPNLScheduleApi.generatePNLSchedule({
      company_name: companyName,
      period_label: '2025 Mar YTD',
      entity_info: 'Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual',
      currency: currencyName,
      scenario: 'Actual',
      show_currency_prefix: false,
      currency_prefix: currencyPrefix,
      convert_to_lakh: true
    });

      toast.dismiss('generating');
      
      if (result.success) {
        toast.success('PNL Schedule generated successfully!');
        await finAnalyzerPNLScheduleApi.triggerPNLScheduleDownload(companyName);
      } else {
        toast.error(result.message || 'Failed to generate PNL Schedule');
      }
    } catch (err: any) {
      toast.dismiss('generating');
      console.error('Error generating PNL Schedule:', err);
      toast.error(err.response?.data?.detail || 'Failed to generate PNL Schedule');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCashFlowFinalyzer = async () => {
    const cashFlowReadiness = readiness as CashFlowFinalizerReadinessResponse;
    if (!cashFlowReadiness?.is_ready) {
      toast.error('Please generate Cash Flow Statement note first');
      return;
    }

    setLoading(true);
    try {
      toast.loading('Generating Cash Flow Finalyzer...', { id: 'generating' });
      
      const result = await cashFlowFinalizerApi.generateCashFlowFinalyzer({
        company_name: companyName,
        period_label: '2025 Mar YTD',
        entity_info: 'Entity: CPM  Book: 8937,IndAS - IndAS entities,Standalone,MYR,Actual',
      currency: currencyName,
      scenario: 'Cashflow'
    });

      toast.dismiss('generating');
      
      if (result.success) {
        toast.success(`Cash Flow Finalyzer generated successfully! (${result.items_extracted} items extracted)`);
        await cashFlowFinalizerApi.triggerCashFlowFinalizerDownload(companyName);
      } else {
        toast.error(result.message || 'Failed to generate Cash Flow Finalyzer');
      }
    } catch (err: any) {
      toast.dismiss('generating');
      console.error('Error generating Cash Flow Finalyzer:', err);
      toast.error(err.response?.data?.detail || 'Failed to generate Cash Flow Finalyzer');
    } finally {
      setLoading(false);
    }
  };

const handleGenerateReport = async (category: FinAnalyzerCategory) => {
  if (category.id === 'finanalyzer-pl') {
    await handleGeneratePNLFinalyzer();
  } else if (category.id === 'finanalyzer-pl-schedule') {
    await handleGeneratePNLSchedule();
  } else if (category.id === 'finanalyzer-cashflow') {
    await handleGenerateCashFlowFinalyzer();
  } else if (category.id === 'finanalyzer-bs') {
    await handleGenerateBSFinalyzer();
  } else if (category.id === 'finanalyzer-bs-schedule') {
    await handleGenerateBSSchedule();
  } else if (category.id === 'finanalyzer-equity') {
    await handleGenerateEquitySchedule();
  } else {
    toast.error(`${category.name} is not yet implemented`);
  }
};
  // Check if readiness is for PNL (has missing_notes property)
  const isPNLReadiness = (r: any): r is StatementReadinessResponse => {
    return r && 'missing_notes' in r;
  };

  // Check if readiness is for Cash Flow (has markdown_file property)
  const isCashFlowReadiness = (r: any): r is CashFlowFinalizerReadinessResponse => {
    return r && 'markdown_file' in r;
  };

  // Render category selection
  if (!selectedCategory) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r rounded-lg shadow-soft" style={{ background: 'linear-gradient(to right, rgb(139, 0, 16), rgb(110, 0, 13))' }}>
          <div className="px-6 py-8">
            <div className="flex items-center">
              <DocumentTextIcon className="h-12 w-12 text-white" />
              <div className="ml-4">
                <h1 className="text-3xl font-bold text-white font-satoshi">
                  Generate FinAnalyzer Reports
                </h1>
                <p className="mt-2 text-white text-opacity-90 font-satoshi">
                  Part 3: FinAnalyzer Web Reports
                </p>
              </div>
            </div>
          </div>
        </div>

        <FinAnalyzerCategorySelection
          companyName={companyName}
          categories={categories}
          onSelectCategory={handleSelectCategory}
          onBack={() => navigate('/step9')}
        />

        {currencyContextCard}

        {/* Navigation */}
        <div className="card">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/step9')}
              className="btn-secondary"
            >
              ← Back to Step 9
            </button>
            <button
              onClick={() => navigate('/feedback')}
              className="btn-primary"
            >
              Continue to Support →
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render selected category (report generation view)
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r rounded-lg shadow-soft" style={{ background: 'linear-gradient(to right, rgb(139, 0, 16), rgb(110, 0, 13))' }}>
        <div className="px-6 py-8">
          <div className="flex items-center">
            <DocumentTextIcon className="h-12 w-12 text-white" />
            <div className="ml-4">
              <h1 className="text-3xl font-bold text-white font-satoshi">
                {selectedCategory.name}
              </h1>
              <p className="mt-2 text-white text-opacity-90 font-satoshi">
                {selectedCategory.description}
              </p>
            </div>
          </div>
        </div>
      </div>

      {currencyContextCard}

      {/* Readiness Check */}
{(selectedCategory.id === 'finanalyzer-pl' || 
  selectedCategory.id === 'finanalyzer-pl-schedule' || 
  selectedCategory.id === 'finanalyzer-cashflow' ||
  selectedCategory.id === 'finanalyzer-bs' ||
  selectedCategory.id === 'finanalyzer-bs-schedule' ||
  selectedCategory.id === 'finanalyzer-equity') && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-gray-900 mb-4 font-satoshi">
            Report Readiness Check
          </h3>
          
          {checkingReadiness ? (
            <div className="flex items-center gap-3 text-gray-600">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900"></div>
              <span className="font-satoshi">Checking readiness...</span>
            </div>
          ) : readiness ? (
            <div className="space-y-4">
              {/* Overall Status */}
              <div className="flex items-center gap-3">
                {readiness.is_ready ? (
                  <>
                    <CheckCircleIcon className="w-6 h-6 text-green-600" />
                    <span className="text-green-600 font-semibold font-satoshi">
                      Ready to generate
                    </span>
                  </>
                ) : (
                  <>
                    <XCircleIcon className="w-6 h-6 text-red-600" />
                    <span className="text-red-600 font-semibold font-satoshi">
                      {isCashFlowReadiness(readiness) 
                        ? 'Cash Flow Statement markdown not found' 
                        : 'Missing required notes'}
                    </span>
                  </>
                )}
              </div>

              {/* PNL Readiness Details */}
              {isPNLReadiness(readiness) && (
                <>
                  {/* Progress Bar */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-600 font-satoshi">
                        Completeness
                      </span>
                      <span className="text-sm font-semibold text-gray-900 font-satoshi">
                        {readiness.completeness_percentage}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full transition-all"
                        style={{
                          width: `${readiness.completeness_percentage}%`,
                          backgroundColor: readiness.is_ready ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'
                        }}
                      />
                    </div>
                  </div>

                  {/* Notes Summary */}
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="text-2xl font-bold text-green-600 font-satoshi">
                        {readiness.total_found}
                      </div>
                      <div className="text-sm text-gray-600 font-satoshi">
                        Found Notes
                      </div>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <div className="text-2xl font-bold text-red-600 font-satoshi">
                        {readiness.missing_notes.length}
                      </div>
                      <div className="text-sm text-gray-600 font-satoshi">
                        Missing Notes
                      </div>
                    </div>
                  </div>

                  {/* Missing Notes List */}
                  {readiness.missing_notes.length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="text-sm font-semibold text-red-900 mb-2 font-satoshi">
                        Missing Notes:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {readiness.missing_notes.map((note) => (
                          <span
                            key={note}
                            className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium font-satoshi"
                          >
                            Note {note}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Cash Flow Readiness Details */}
              {isCashFlowReadiness(readiness) && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-gray-700 font-satoshi">
                    {readiness.message}
                  </p>
                  {readiness.markdown_file && (
                    <p className="text-xs text-gray-500 mt-2 font-mono">
                      Source: {readiness.markdown_file}
                    </p>
                  )}
                </div>
              )}
            </div>
          ) : (
<button
  onClick={() => {
    if (selectedCategory.id === 'finanalyzer-pl') checkPNLReadiness();
    else if (selectedCategory.id === 'finanalyzer-pl-schedule') checkPNLScheduleReadiness();
    else if (selectedCategory.id === 'finanalyzer-cashflow') checkCashFlowReadiness();
    else if (selectedCategory.id === 'finanalyzer-bs') checkBSFinalizerReadiness();
    else if (selectedCategory.id === 'finanalyzer-bs-schedule') checkBSScheduleReadiness();
    else if (selectedCategory.id === 'finanalyzer-equity') checkEquityScheduleReadiness();
  }}
  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md font-medium transition-colors font-satoshi"
>
  Check Readiness
</button>
          )}
        </div>
      )}

      {/* Report Generation Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-8 shadow-sm">
        <div className="text-center">
          <div className="text-6xl mb-4">{selectedCategory.icon}</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2 font-satoshi">
            {selectedCategory.name}
          </h2>
          <p className="text-gray-600 mb-6 font-satoshi">
            {selectedCategory.description}
          </p>
          
          <div className="flex gap-4 justify-center">
            <button
              onClick={handleBackToCategories}
              className="px-6 py-3 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors font-medium font-satoshi"
            >
              Back to Reports
            </button>
            <button
              onClick={() => handleGenerateReport(selectedCategory)}
              disabled={loading || !readiness?.is_ready}
              className="px-6 py-3 rounded-md text-white font-medium transition-all font-satoshi disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                backgroundColor: loading ? '#9ca3af' : 'rgb(139, 0, 16)',
              }}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Generating...
                </span>
              ) : (
                'Generate Report'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/step9')}
            className="btn-secondary"
          >
            ← Back to Step 9
          </button>
          <button
            onClick={() => navigate('/feedback')}
            className="btn-primary"
          >
            Continue to Support →
          </button>
        </div>
      </div>
    </div>
  );
};

export default FinAnalyzerReportsPage;
