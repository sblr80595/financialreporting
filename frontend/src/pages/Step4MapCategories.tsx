import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from 'react-query';
import {
  TagIcon,
  ArrowRightIcon,
  CloudArrowUpIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import FileUpload from '../components/FileUpload';
import FileManager from '../components/FileManager';
import FinalTBSummary from '../components/FinalTBSummary';
import { apiService } from '../services/api';
import { useEntity } from '../contexts/EntityContext';
import { useCurrencySelection } from '../contexts/CurrencySelectionContext';

const Step4MapCategories: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();
  const [mappingResult, setMappingResult] = useState<any>(null);
  const [uploadedMappingFile, setUploadedMappingFile] = useState<File | null>(null);
  const {
    currencyInfo: ctxCurrencyInfo,
    fxRates,
    selectedCurrency: ctxSelectedCurrency,
    setSelectedCurrencyCode,
  } = useCurrencySelection();
  const currencyInfo = ctxCurrencyInfo || undefined;
  const selectedCurrency = ctxSelectedCurrency || undefined;

  // Check for existing files - AUTO FETCH on mount
  const { data: filesData, refetch: refetchFiles, isLoading: isLoadingFiles } = useQuery(
    ['entity-files', getCompanyName()],
    () => apiService.listEntityFiles(getCompanyName()),
    {
      enabled: true,
      refetchOnMount: 'always', // Always refetch when component mounts
      refetchOnWindowFocus: false,
      staleTime: 0, // Always consider data stale to ensure refetch
      cacheTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
      onSuccess: (response) => {
        console.log('[Step 4] Full API response:', response);
        console.log('[Step 4] Response data:', response.data);
      },
      onError: (error) => {
        console.error('[Step 4] Error fetching files:', error);
      }
    }
  );

  // Helper function to extract filename from string or object
  const getFilename = (file: string | { filename: string }): string => {
    return typeof file === 'string' ? file : file.filename;
  };

  // Get existing files from query data
  const configFiles = filesData?.data?.config || [];
  const existingMappingFiles = configFiles.filter((f: string | { filename: string }) => {
    const filename = getFilename(f).toLowerCase();
    return filename.includes('glcode_major_minor_mappings') ||
      filename.includes('mapping') ||
      filename.includes('glcode');
  });

  const adjustedFiles = filesData?.data?.adjusted_trialbalance || [];
  const existingAdjustedTB = adjustedFiles.filter((f: string | { filename: string }) => {
    const filename = getFilename(f).toLowerCase();
    return filename.includes('adjusted') && !filename.includes('final');
  });
  const existingFinalTB = adjustedFiles.filter((f: string | { filename: string }) => {
    const filename = getFilename(f).toLowerCase();
    return filename.includes('final');
  });

  const uploadMappingMutation = useMutation(
    (file: File) => {
      return apiService.uploadConfigFile(getCompanyName(), file);
    },
    {
      onSuccess: () => {
        toast.success('Mapping file uploaded successfully!');
        refetchFiles();
        setUploadedMappingFile(null);
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Upload failed');
      },
    }
  );

  const mappingMutation = useMutation(
    (entity: string) => apiService.startCategoryMapping(entity),
    {
      onSuccess: (response) => {
        setMappingResult(response.data);
        if (response.data.success) {
          toast.success(response.data.message || 'Categories mapped successfully!');
          refetchFiles();
        } else {
          toast.error(response.data.message || 'Mapping completed with errors');
        }
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Mapping failed');
      },
    }
  );

  const handleMapping = () => {
    mappingMutation.mutate(getCompanyName());
  };

  const handleSkipToNext = () => {
    toast.success('Proceeding with existing files');
    navigate('/step5');
  };

  const handleMappingFileSelect = (files: File[]) => {
    if (files.length > 0) {
      setUploadedMappingFile(files[0]);
    }
  };

  const handleUploadMapping = () => {
    if (!uploadedMappingFile) {
      toast.error('Please select a mapping file first');
      return;
    }
    uploadMappingMutation.mutate(uploadedMappingFile);
  };

  const canProceed = existingMappingFiles.length > 0 && existingAdjustedTB.length > 0;

  // Fetch final TB summary if final TB exists
  const { data: finalTBSummary } = useQuery(
    ['final-tb-summary', getCompanyName()],
    () => apiService.getFinalTBSummary(getCompanyName()),
    {
      enabled: existingFinalTB.length > 0,
      staleTime: 2 * 60 * 1000,
    }
  );

  return (
    <div className="space-y-6">
      {currencyInfo && (
        <div className="card flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs text-gray-500">Local currency</p>
              <p className="text-sm font-semibold text-gray-900">
                {currencyInfo.currency_symbol} ({currencyInfo.default_currency}) — {currencyInfo.currency_name}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">View currency:</span>
              <div className="inline-flex rounded-md shadow-sm overflow-hidden border border-gray-200">
                {[currencyInfo.default_currency, 'USD', 'INR'].map((code) => (
                  <button
                    key={code}
                    onClick={() => setSelectedCurrencyCode(code)}
                    className={`px-3 py-1 text-xs ${
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
            </div>
          {fxRates.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {fxRates.map((rate) => (
                <div
                  key={`${rate.base_currency}-${rate.target_currency}`}
                  className="inline-flex items-center border border-gray-200 rounded-md px-3 py-1 bg-gray-50 text-xs text-gray-700"
                >
                  <span>1 {rate.base_currency}</span>
                  <span className="mx-1 text-gray-400">→</span>
                  <span className="font-semibold">
                    {new Intl.NumberFormat('en-US', { maximumFractionDigits: 4 }).format(rate.rate)} {rate.target_currency}
                  </span>
                  <span className="ml-2 text-[10px] text-gray-500">{rate.source}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {isLoadingFiles && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <p className="text-blue-700">Checking for existing files...</p>
          </div>
        </div>
      )}

      {!isLoadingFiles && existingFinalTB.length > 0 && !mappingResult && (
        <div className="card bg-green-50 border-2 border-green-300">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <div>
                <h3 className="text-lg font-semibold text-green-900">
                  Category Mapping Report
                </h3>
                <p className="text-sm text-green-700">
                  {existingFinalTB.length} file(s) available • Ready to proceed to Step 5
                </p>
              </div>
            </div>
            <button
              onClick={handleSkipToNext}
              className="btn-primary bg-green-600 hover:bg-green-700 flex items-center space-x-2"
            >
              <span>Continue to Step 5</span>
              <ArrowRightIcon className="h-5 w-5" />
            </button>
          </div>

          <div className="bg-white rounded border border-green-200 p-4">
            <FileManager
              files={existingFinalTB}
              folderType="adjusted_trialbalance"
              entity={getCompanyName()}
              onDelete={refetchFiles}
            />
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {existingMappingFiles.length > 0 ? 'Mapping Configuration' : 'Upload Mapping File'}
        </h2>

        {/* <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">📍 Standard Location & Filename</h3>
          <code className="text-xs bg-white px-2 py-1 rounded block text-blue-800">
            data/{getCompanyName()}/input/config/glcode_major_minor_mappings.xlsx
          </code>
          <p className="text-xs text-blue-700 mt-2">
            All uploaded files will be saved with this standard filename for consistency
          </p>
        </div> */}

        {existingMappingFiles.length > 0 ? (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded">
            <div className="flex items-center">
              <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" />
              <div>
                <p className="text-sm font-medium text-green-900">
                  Current mapping file: {getFilename(existingMappingFiles[0])}
                </p>
                <p className="text-xs text-green-700">
                  You can upload a new file to replace the existing one
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-sm text-yellow-800">
              <strong>⚠️ No mapping file found.</strong> Please upload the GL Code mapping file to proceed.
            </p>
          </div>
        )}

        <FileUpload
          onFilesSelected={handleMappingFileSelect}
          acceptedTypes={['.xlsx', '.xls']}
          multiple={false}
          maxFiles={1}
        />

        {uploadedMappingFile && (
          <div className="mt-4 p-4 bg-gray-50 rounded border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">{uploadedMappingFile.name}</p>
                <p className="text-xs text-gray-600 mb-1">
                  {(uploadedMappingFile.size / 1024).toFixed(2)} KB
                </p>
                <p className="text-xs text-blue-600">
                  → Will be saved as: glcode_major_minor_mappings.xlsx
                </p>
              </div>
              <button
                onClick={handleUploadMapping}
                disabled={uploadMappingMutation.isLoading}
                className="btn-primary"
              >
                {uploadMappingMutation.isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Uploading...
                  </>
                ) : (
                  <>
                    <CloudArrowUpIcon className="h-5 w-5 mr-2" />
                    Upload & Save
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Show existing config files */}
        {existingMappingFiles.length > 0 && (
          <div className="mt-4 bg-white rounded border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Current Config Files</h3>
            <FileManager
              files={existingMappingFiles}
              folderType="config"
              entity={getCompanyName()}
              onDelete={refetchFiles}
            />
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {existingFinalTB.length > 0 ? 'Re-run Category Mapping' : 'Execute Category Mapping'}
        </h2>

        {!canProceed && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-sm text-yellow-800">
              <strong>Required:</strong> Mapping file and adjusted trial balance (from Step 3)
            </p>
          </div>
        )}

        <button
          onClick={handleMapping}
          disabled={mappingMutation.isLoading || !canProceed}
          className={`btn-primary ${existingFinalTB.length > 0
            ? 'bg-yellow-500 hover:bg-yellow-600'
            : ''
            } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {mappingMutation.isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Mapping...
            </>
          ) : (
            <>
              <TagIcon className="h-5 w-5 mr-2" />
              {existingFinalTB.length > 0 ? '🔄 Re-run Mapping' : '🗂️ Execute Mapping'}
            </>
          )}
        </button>
      </div>

      {mappingResult && (
        <div className="card">
          {mappingResult.success && mappingResult.message && (
            <div className="mb-6 bg-green-50 border-2 border-green-300 rounded-lg p-4">
              <h2 className="text-xl font-bold text-green-800 text-center">{mappingResult.message}</h2>
            </div>
          )}

          <h2 className="text-lg font-semibold text-gray-900 mb-4">📊 Mapping Results</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg text-center border-2 border-gray-200">
              <div className="text-2xl font-bold text-gray-900">{mappingResult.mapping_summary?.total_records || 0}</div>
              <div className="text-sm text-gray-500">Total GL Codes</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center border-2 border-green-300">
              <div className="text-2xl font-bold text-green-600">{mappingResult.mapping_summary?.mapped_records || 0}</div>
              <div className="text-sm text-green-600">Successfully Mapped</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center border-2 border-red-300">
              <div className="text-2xl font-bold text-red-600">{mappingResult.mapping_summary?.unmapped_records || 0}</div>
              <div className="text-sm text-red-600">Unmapped</div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg text-center border-2 border-blue-300">
              <div className="text-2xl font-bold text-blue-600">{mappingResult.mapping_summary?.mapping_percentage || 0}%</div>
              <div className="text-sm text-blue-600">Mapping Rate</div>
            </div>
          </div>

          {mappingResult.output_file && (
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 border-2 border-blue-300 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-bold text-blue-900 mb-3">📄 Mapped Trial Balance Generated</h3>
              <p className="text-sm text-blue-700 mb-4">
                GL Codes have been mapped to Major and Minor categories
              </p>
              {mappingResult.download_url && (
                <button
                  onClick={async () => {
                    try {
                      const response = await apiService.downloadMappingFile(getCompanyName(), 'final_trialbalance.xlsx');
                      const url = window.URL.createObjectURL(new Blob([response.data]));
                      const link = document.createElement('a');
                      link.href = url;
                      link.setAttribute('download', 'final_trialbalance.xlsx');
                      document.body.appendChild(link);
                      link.click();
                      link.remove();
                      window.URL.revokeObjectURL(url);
                      toast.success('Downloaded final trial balance');
                    } catch (error) {
                      toast.error('Failed to download file');
                    }
                  }}
                  className="btn-primary flex items-center space-x-2"
                >
                  <CloudArrowUpIcon className="h-5 w-5" />
                  <span>Download Final Trial Balance</span>
                </button>
              )}
            </div>
          )}

          {mappingResult.next_step?.available && (
            <div className="bg-gradient-to-r from-green-50 to-green-100 border-2 border-green-300 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-green-900">{mappingResult.next_step.next_step_label}</h4>
                  <p className="text-sm text-green-700">{mappingResult.next_step.next_step_description}</p>
                </div>
                <button
                  onClick={() => navigate('/step5')}
                  className="btn-primary flex items-center space-x-2"
                >
                  <span>Next Step</span>
                  <ArrowRightIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Final TB Summary Section */}
      {existingFinalTB.length > 0 && finalTBSummary?.data && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
          <FinalTBSummary
            entity={getCompanyName()}
            data={finalTBSummary.data}
            currencyInfo={currencyInfo}
            selectedCurrency={selectedCurrency}
            fxRates={fxRates}
          />
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/step3')}
            className="btn-secondary"
          >
            ← Back to Step 3
          </button>

          {mappingResult && (
            <button
              onClick={() => navigate('/step5')}
              className="btn-primary"
            >
              Continue to Step 5 →
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Step4MapCategories;
