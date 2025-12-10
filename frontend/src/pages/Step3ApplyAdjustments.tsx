import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from 'react-query';
import {
  PlayIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';
import { useEntity } from '../contexts/EntityContext';
import { usePeriod } from '../contexts/PeriodContext';
import AdjustmentsPreview from './AdjustmentsPreview';
import FileManager from '../components/FileManager';
import { useCurrencySelection } from '../contexts/CurrencySelectionContext';


const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';

const Step3ApplyAdjustments: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();
  const { currentPeriod, currentPeriodColumn } = usePeriod();
  const [processingId, setProcessingId] = useState<string | null>(null);
  const {
    currencyInfo: ctxCurrencyInfo,
    fxRates,
    selectedCurrency: ctxSelectedCurrency,
    setSelectedCurrencyCode
  } = useCurrencySelection();
  const currencyInfo = ctxCurrencyInfo || undefined;
  const selectedCurrency = ctxSelectedCurrency || undefined;

  // Check for existing adjusted files in output folder
  const { data: filesData, refetch: refetchFiles } = useQuery(
    ['entity-files', getCompanyName()],
    () => apiService.listEntityFiles(getCompanyName()),
    {
      enabled: true,
      refetchOnMount: 'always',
      refetchOnWindowFocus: false,
      staleTime: 0,
    }
  );

  // Get adjusted trial balance files from output/adjusted-trialbalance folder
  const existingAdjustedFiles = filesData?.data?.adjusted_trialbalance || [];

  // Filter to only show adjusted_trialbalance.xlsx - exclude final_trialbalance and validation reports
  const adjustedTrialBalanceFiles = existingAdjustedFiles.filter((file: any) => {
    const filename = typeof file === 'string' ? file : file.filename;
    const lowerFilename = filename.toLowerCase();

    // Only show adjusted_trialbalance.xlsx (the output from Step 3)
    // Exclude: final_trialbalance.xlsx (from Step 4), validation reports (from Step 5), JSON files
    return (
      (filename.endsWith('.xlsx') || filename.endsWith('.xls') || filename.endsWith('.xlsb')) &&
      lowerFilename.includes('adjusted') &&
      !lowerFilename.includes('final') &&
      !lowerFilename.includes('validation') &&
      !lowerFilename.includes('.json')
    );
  });

  const hasAdjustedFile = adjustedTrialBalanceFiles.length > 0;

  // Process adjustments mutation
  const processMutation = useMutation(
    (entity: string) => apiService.processAdjustments(entity, {
      periodKey: currentPeriod || undefined,
      periodColumn: currentPeriodColumn || undefined,
    }),
    {
      onSuccess: (response) => {
        setProcessingId(response.data.processing_id);
        toast.success('Adjustment processing started!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to start processing');
      },
    }
  );

  // Poll processing status
  const { data: statusResponse } = useQuery(
    ['processing-status', processingId],
    () => apiService.getProcessingStatus(processingId!),
    {
      enabled: !!processingId,
      refetchInterval: (data) => {
        const status = data?.data?.status;
        if (status === 'completed') {
          toast.success('Adjustments applied successfully!');
          refetchFiles();
          // Refetch impact summary after a short delay to ensure file is ready
          setTimeout(() => {
            refetchImpactSummary();
          }, 1000);
          setProcessingId(null);
          return false;
        }
        if (status === 'failed') {
          toast.error('Adjustment processing failed');
          setProcessingId(null);
          return false;
        }
        return 2000;
      },
    }
  );

  const status = statusResponse?.data;
  const isProcessing = !!processingId && status?.status === 'processing';

  // Fetch currency info for the selected entity
  const convertValue = (value: number): number => {
    if (!currencyInfo || !selectedCurrency) return value;
    const baseCode = currencyInfo.default_currency.toUpperCase();
    const targetCode = selectedCurrency.default_currency.toUpperCase();
    if (baseCode === targetCode) return value;
    const rate = fxRates.find((r) => r.target_currency === targetCode);
    if (!rate) return value;
    return value * rate.rate;
  };

  // Fetch adjustment impact summary (only if adjusted file exists)
  const { data: impactSummary, refetch: refetchImpactSummary } = useQuery(
    ['adjustment-impact', getCompanyName()],
    async () => {
      const response = await apiService.getAdjustmentImpactSummary(getCompanyName());
      return response.data;
    },
    {
      enabled: hasAdjustedFile,
      staleTime: 2 * 60 * 1000, // Cache for 2 minutes
    }
  );

  const handleApplyAdjustments = () => {
    processMutation.mutate(getCompanyName());
  };

  const handleNext = () => {
    navigate('/step4');
  };

  return (
    <div className="space-y-6">
      {/* Adjustments Preview with Integrated Impact Tab */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <AdjustmentsPreview
          currencyInfoProp={currencyInfo}
          fxRatesProp={fxRates}
          selectedCurrencyCode={selectedCurrency?.default_currency || currencyInfo?.default_currency}
          onCurrencyChange={setSelectedCurrencyCode}
          impactSummary={hasAdjustedFile ? impactSummary : undefined}
          convertValue={convertValue}
        />
      </div>

      {/* Apply Adjustments Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 font-satoshi">
          Apply All Adjustments
        </h2>

        {/* Show existing adjusted file if available */}
        {hasAdjustedFile && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <CheckCircleIcon className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-green-900 mb-2 font-satoshi">
                  Adjusted Trial Balance Already Exists
                </h3>
                <FileManager
                  files={adjustedTrialBalanceFiles}
                  folderType="adjusted_trialbalance"
                  entity={getCompanyName()}
                  onDelete={() => refetchFiles()}
                  showActions={true}
                />
                <p className="text-sm text-green-700 mt-2 font-satoshi">
                  You can re-apply adjustments if needed, or proceed to the next step.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Apply Adjustments Button */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleApplyAdjustments}
            disabled={isProcessing}
            className="flex items-center gap-2 px-6 py-3 rounded-md transition-all font-medium shadow-sm text-white font-satoshi disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              backgroundColor: isProcessing ? '#9ca3af' : PLAINFLOW_RED,
              cursor: isProcessing ? 'not-allowed' : 'pointer'
            }}
            onMouseEnter={(e) => {
              if (!isProcessing) {
                e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER;
              }
            }}
            onMouseLeave={(e) => {
              if (!isProcessing) {
                e.currentTarget.style.backgroundColor = PLAINFLOW_RED;
              }
            }}
          >
            {isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Processing...
              </>
            ) : (
              <>
                <PlayIcon className="w-5 h-5" />
                {hasAdjustedFile ? 'Re-apply All Adjustments' : 'Apply All Adjustments'}
              </>
            )}
          </button>

          {status && (
            <div className="text-sm text-gray-600 font-satoshi">
              Status: <span className="font-medium">{status.status}</span>
              {status.progress !== undefined && (
                <span className="ml-2">({Math.round(status.progress)}%)</span>
              )}
            </div>
          )}
        </div>

        {/* Processing Progress */}
        {isProcessing && status && (
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${status.progress || 0}%`,
                  backgroundColor: PLAINFLOW_RED
                }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-2 font-satoshi">
              Processing adjustments...
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center">
        <button
          onClick={() => navigate('/step2')}
          className="btn-secondary"
        >
          ← Back to Step 2
        </button>

        <button
          onClick={handleNext}
          className="btn-primary"
        >
          Continue to Step 4 →
        </button>
      </div>
    </div>
  );
};

export default Step3ApplyAdjustments;
