import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { useEntity } from '../contexts/EntityContext';
import { apiService } from '../services/api';
import { formatCurrency } from '../utils/currencyFormatter';
import { CurrencyContext, CurrencyInfo } from '../types/currency';
import AdjustmentImpactSummary from '../components/AdjustmentImpactSummary';
import {
  ChartBarIcon,
  DocumentTextIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';

interface AdjustmentSummary {
  classification: string;
  count: number;
  total_debit: number;
  total_credit: number;
  net_impact: number;
}

interface AdjustmentDetail {
  account: string;
  debit: number;
  credit: number;
  description: string;
  schedule_iii_head: string;
  compliance_impact: string;
  adjustment_classification: string;
  compliance_standard: string;
  file_source: string;
}

interface AdjustmentAnalysisResponse {
  entity: string;
  total_adjustments: number;
  total_files: number;
  summary_by_classification: AdjustmentSummary[];
  summary_by_schedule_iii: any[];
  adjustments: AdjustmentDetail[];
}

interface Props {
  currencyInfoProp?: CurrencyInfo;
  fxRatesProp?: CurrencyContext['rates'];
  selectedCurrencyCode?: string | null;
  onCurrencyChange?: (code: string) => void;
  impactSummary?: any;
  convertValue?: (value: number) => number;
  adjustmentsData?: AdjustmentAnalysisResponse;
}

const AdjustmentsPreview: React.FC<Props> = ({
  currencyInfoProp,
  fxRatesProp,
  selectedCurrencyCode,
  onCurrencyChange,
  impactSummary,
  convertValue: convertValueProp,
  adjustmentsData: adjustmentsDataProp,
}) => {
  const { selectedEntity } = useEntity();
  const [selectedClassification, setSelectedClassification] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'summary' | 'impact' | 'details'>('summary');
  const [internalSelectedCurrencyCode, setInternalSelectedCurrencyCode] = useState<string | null>(selectedCurrencyCode ?? null);

  // Keep internal state in sync with parent-driven selection
  useEffect(() => {
    setInternalSelectedCurrencyCode(selectedCurrencyCode ?? null);
  }, [selectedCurrencyCode]);

  const { data, isLoading, error } = useQuery<AdjustmentAnalysisResponse>(
    ['adjustments-analysis', selectedEntity],
    async () => {
      const response = await apiService.getAdjustmentsAnalysis(selectedEntity);
      return response.data;
    },
    {
      enabled: !!selectedEntity,
      staleTime: 2 * 60 * 1000, // Cache for 2 minutes
    }
  );

  // Use provided adjustments data or fetched data
  const adjustmentsData = adjustmentsDataProp || data;

  // Fetch currency context (local + reporting FX)
  const shouldFetchCurrencyContext = !currencyInfoProp;
  const { data: currencyContext, refetch: refetchCurrencyContext } = useQuery<CurrencyContext>(
    ['currency-context', selectedEntity, internalSelectedCurrencyCode],
    async () => {
      const forceRefresh =
        !!internalSelectedCurrencyCode &&
        currencyInfo &&
        internalSelectedCurrencyCode !== currencyInfo.default_currency;
      return await apiService.getCurrencyContext(selectedEntity, ['USD', 'INR'], forceRefresh);
    },
    {
      enabled: !!selectedEntity && shouldFetchCurrencyContext,
      staleTime: 0,
      refetchOnWindowFocus: false,
    }
  );
  const currencyInfo: CurrencyInfo | undefined = currencyInfoProp ?? currencyContext?.local_currency;
  const fxRates = fxRatesProp ?? currencyContext?.rates ?? [];

  useEffect(() => {
    if (
      selectedCurrencyCode &&
      currencyInfo &&
      internalSelectedCurrencyCode !== currencyInfo.default_currency
    ) {
      refetchCurrencyContext();
    }
  }, [internalSelectedCurrencyCode, currencyInfo, refetchCurrencyContext, selectedCurrencyCode]);

  const getCurrencyInfoForCode = (code?: string | null): CurrencyInfo | undefined => {
    if (!code) return currencyInfo;
    const upper = code.toUpperCase();
    if (upper === currencyInfo?.default_currency?.toUpperCase()) return currencyInfo;
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
    return known[upper];
  };

  const selectedCurrency =
    getCurrencyInfoForCode(internalSelectedCurrencyCode) || currencyInfo;

  const convertValue = (value: number): number => {
    if (!selectedCurrency || !currencyInfo) return value;
    const baseCode = currencyInfo.default_currency.toUpperCase();
    const targetCode = selectedCurrency.default_currency.toUpperCase();
    if (baseCode === targetCode) return value;
    const rate = fxRates.find((r) => r.target_currency === targetCode);
    if (!rate) return value;
    return value * rate.rate;
  };

  const getClassificationColor = (classification: string) => {
    const colors: Record<string, string> = {
      'Accruals and Deferrals': 'bg-blue-100 text-blue-800 border-blue-200',
      'Reclassification': 'bg-purple-100 text-purple-800 border-purple-200',
      'Depreciation and Amortization': 'bg-orange-100 text-orange-800 border-orange-200',
      'Provisions and Impairments': 'bg-red-100 text-red-800 border-red-200',
      'Inventory Adjustments': 'bg-green-100 text-green-800 border-green-200',
      'Foreign Exchange Adjustments': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'Intercompany Eliminations': 'bg-pink-100 text-pink-800 border-pink-200',
      'Revenue Recognition Adjustments': 'bg-indigo-100 text-indigo-800 border-indigo-200',
      'Tax Adjustments': 'bg-teal-100 text-teal-800 border-teal-200',
      'Prior Period Adjustments': 'bg-gray-100 text-gray-800 border-gray-200',
      'Period Cutoff Adjustments': 'bg-amber-100 text-amber-800 border-amber-200',
      'Audit Adjustments': 'bg-cyan-100 text-cyan-800 border-cyan-200',
      'Other Adjustments': 'bg-slate-100 text-slate-800 border-slate-200',
    };
    return colors[classification] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error Loading Adjustments</h3>
        <p className="text-red-600">
          {(error as any)?.response?.data?.detail || 'Failed to load adjustment analysis'}
        </p>
      </div>
    );
  }

  if (!adjustmentsData) {
    return null;
  }

  // Check if no adjustments available
  if (adjustmentsData.total_adjustments === 0) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Adjustments Preview</h1>
              <p className="mt-1 text-sm text-gray-500">
                Industry-standard classification and analysis of manual adjustments
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-gray-500">Entity</p>
                <p className="text-lg font-semibold text-gray-900">{selectedEntity?.toUpperCase()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* No Adjustments Message */}
        <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-8 text-center">
          <DocumentTextIcon className="h-16 w-16 text-yellow-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-yellow-900 mb-2">
            No Adjustment Files Available
          </h3>
          <p className="text-yellow-700 mb-4">
            No manual adjustment files were found for entity <strong>{selectedEntity?.toUpperCase()}</strong>.
          </p>
          <div className="bg-white rounded-md p-4 text-left max-w-md mx-auto">
            <p className="text-sm text-gray-600 mb-2">
              <strong>Expected location:</strong>
            </p>
            <code className="text-xs bg-gray-100 px-2 py-1 rounded block">
              data/{selectedEntity}/input/manual-adjustments/*.xlsx
            </code>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Adjustments Preview</h1>
            <p className="mt-1 text-sm text-gray-500">
              Industry-standard classification and analysis of manual adjustments
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-gray-500">Entity</p>
              <p className="text-lg font-semibold text-gray-900">{adjustmentsData.entity.toUpperCase()}</p>
            </div>
            {currencyInfo && (
              <div className="text-right">
                <p className="text-sm text-gray-500">View currency</p>
                <div className="inline-flex rounded-md shadow-sm overflow-hidden border border-gray-200">
                  {[currencyInfo.default_currency, 'USD', 'INR'].map((code) => (
                    <button
                      key={code}
                      onClick={() => {
                        onCurrencyChange?.(code);
                        setInternalSelectedCurrencyCode(code);
                      }}
                      className={`px-2 py-1 text-xs ${
                        (selectedCurrency?.default_currency || currencyInfo.default_currency) === code
                          ? 'bg-primary-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-50'
                      } border-r border-gray-200 last:border-0`}
                    >
                      {code}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {currencyInfo && (
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="border border-gray-200 rounded-md p-4 bg-gray-50">
              <p className="text-sm text-gray-500">Local currency</p>
              <p className="text-lg font-semibold text-gray-900">
                {currencyInfo.currency_symbol} ({currencyInfo.default_currency}) — {currencyInfo.currency_name}
              </p>
              <p className="text-xs text-gray-500">Entity: {currencyInfo.entity_name}</p>
              <p className="text-xs text-gray-500 mt-1">
                Viewing in: {selectedCurrency?.currency_symbol} {selectedCurrency?.default_currency}
              </p>
            </div>
            <div className="sm:col-span-2 border border-gray-200 rounded-md p-4 bg-white">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-700">Reporting (USD / INR)</p>
                {currencyContext?.last_refreshed && (
                  <p className="text-xs text-gray-500">
                    Updated {new Date(currencyContext.last_refreshed).toLocaleString()}
                  </p>
                )}
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
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
                  <span className="text-xs text-gray-500">FX rates unavailable. Showing local currency.</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Stats Row */}
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-3">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 overflow-hidden rounded-lg border border-blue-200">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DocumentTextIcon className="h-8 w-8 text-blue-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-blue-700 truncate">Total Adjustments</dt>
                    <dd className="text-3xl font-bold text-blue-900">{adjustmentsData.total_adjustments}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 overflow-hidden rounded-lg border border-purple-200">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <FunnelIcon className="h-8 w-8 text-purple-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-purple-700 truncate">Classifications</dt>
                    <dd className="text-3xl font-bold text-purple-900">
                      {adjustmentsData.summary_by_classification.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 overflow-hidden rounded-lg border border-green-200">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ChartBarIcon className="h-8 w-8 text-green-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-green-700 truncate">Source Files</dt>
                    <dd className="text-3xl font-bold text-green-900">{adjustmentsData.total_files}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white shadow rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
            <button
              onClick={() => setSelectedTab('summary')}
              className={`${
                selectedTab === 'summary'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Summary by Classification
            </button>
            <button
              onClick={() => setSelectedTab('impact')}
              className={`${
                selectedTab === 'impact'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Adjustment Impact
            </button>
            {/* Commented out - Adjustment Impact view provides same functionality with filtering */}
            {/* <button
              onClick={() => setSelectedTab('details')}
              className={`${
                selectedTab === 'details'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Detailed Adjustments
            </button> */}
          </nav>
        </div>

        {/* Summary Tab */}
        {selectedTab === 'summary' && (
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {adjustmentsData.summary_by_classification.map((summary, index) => (
                <div
                  key={index}
                  className={`border-2 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer ${getClassificationColor(
                    summary.classification
                  )} ${
                    selectedClassification === summary.classification
                      ? 'ring-2 ring-primary-500 ring-offset-2'
                      : ''
                  }`}
                  onClick={() => {
                    setSelectedClassification(
                      selectedClassification === summary.classification
                        ? null
                        : summary.classification
                    );
                    // Switch to Adjustment Impact tab when a classification is selected
                    setSelectedTab('impact');
                  }}
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-semibold text-sm">{summary.classification}</h3>
                    <span className="px-2 py-1 text-xs font-bold rounded-full bg-white bg-opacity-50">
                      {summary.count} entries
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <p className="font-medium opacity-75">Debit</p>
                      <p className="font-bold">
                        {formatCurrency(convertValue(summary.total_debit), selectedCurrency)}
                      </p>
                    </div>
                    <div>
                      <p className="font-medium opacity-75">Credit</p>
                      <p className="font-bold">
                        {formatCurrency(convertValue(summary.total_credit), selectedCurrency)}
                      </p>
                    </div>
                    <div>
                      <p className="font-medium opacity-75">Net Impact</p>
                      <div className="flex items-center">
                        {summary.net_impact > 0 ? (
                          <ArrowTrendingUpIcon className="h-3 w-3 mr-1" />
                        ) : summary.net_impact < 0 ? (
                          <ArrowTrendingDownIcon className="h-3 w-3 mr-1" />
                        ) : null}
                        <p className="font-bold">
                          {formatCurrency(convertValue(summary.net_impact), selectedCurrency)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Adjustment Impact Tab */}
        {selectedTab === 'impact' && (
          <div className="p-6">
            {impactSummary ? (
              <>
                {selectedClassification && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <p className="text-sm text-blue-800 font-satoshi">
                      <span className="font-semibold">Filtered by:</span> {selectedClassification}
                    </p>
                  </div>
                )}
                <AdjustmentImpactSummary
                  data={impactSummary}
                  currencyInfo={currencyInfoProp}
                  selectedCurrency={selectedCurrency}
                  fxRates={fxRatesProp || fxRates}
                  convertValue={convertValueProp || convertValue}
                  selectedClassification={selectedClassification}
                  adjustmentsData={adjustmentsData}
                />
              </>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-600 font-satoshi">
                  Adjustment impact will be available after applying adjustments.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdjustmentsPreview;
