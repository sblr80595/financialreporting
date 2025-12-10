import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from 'react-query';
import {
  CloudArrowUpIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import FileUpload from '../components/FileUpload';
import FileManager from '../components/FileManager';
import FinalTBSummary from '../components/FinalTBSummary';
import { apiService } from '../services/api';
import { useEntity } from '../contexts/EntityContext';
import { useCurrencySelection } from '../contexts/CurrencySelectionContext';

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';

const Step4CategoryMapping: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();
  const [mappingResult, setMappingResult] = useState<any>(null);
  const [uploadedMappingFile, setUploadedMappingFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState<'configuration' | 'mappings'>('configuration');
  const {
    currencyInfo: ctxCurrencyInfo,
    fxRates,
    selectedCurrency: ctxSelectedCurrency,
    setSelectedCurrencyCode,
  } = useCurrencySelection();
  const currencyInfo = ctxCurrencyInfo || undefined;
  const selectedCurrency = ctxSelectedCurrency || undefined;

  // Check for existing files
  const { data: filesData, refetch: refetchFiles, isLoading: isLoadingFiles } = useQuery(
    ['entity-files-category-mapping', getCompanyName()],
    () => apiService.listEntityFiles(getCompanyName()),
    {
      enabled: true,
      refetchOnMount: 'always',
      refetchOnWindowFocus: false,
      staleTime: 0,
      cacheTime: 5 * 60 * 1000,
    }
  );

  // Helper function to extract filename
  const getFilename = (file: string | { filename: string }): string => {
    return typeof file === 'string' ? file : file.filename;
  };

  // Get existing files
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
    (file: File) => apiService.uploadConfigFile(getCompanyName(), file),
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
          // Switch to mappings tab after successful mapping
          setActiveTab('mappings');
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

  // Fetch final TB summary
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
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h1 className="text-2xl font-bold text-gray-900 font-satoshi">Category Mapping</h1>
        <p className="text-sm text-gray-600 mt-1 font-satoshi">
          Map GL codes to Major and Minor categories for financial statement generation
        </p>
      </div>

      {/* Currency Info */}
      {currencyInfo && (
        <div className="flex flex-col gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs text-gray-500 font-satoshi">Local currency</p>
              <p className="text-sm font-semibold text-gray-900 font-satoshi">
                {currencyInfo.currency_symbol} ({currencyInfo.default_currency}) — {currencyInfo.currency_name}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 font-satoshi">View currency:</span>
              <div className="inline-flex rounded-md shadow-sm overflow-hidden border border-gray-200">
                {[currencyInfo.default_currency, 'USD', 'INR'].map((code) => (
                  <button
                    key={code}
                    onClick={() => setSelectedCurrencyCode(code)}
                    className={`px-3 py-1 text-xs font-satoshi ${
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
                  className="inline-flex items-center border border-gray-200 rounded-md px-3 py-1 bg-white text-xs text-gray-700 font-satoshi"
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

      {/* Tabs */}
      <div className="bg-white rounded-t-lg border border-b-0 border-gray-200 shadow-sm">
        <div className="flex">
          <button
            onClick={() => setActiveTab('configuration')}
            className={`
              relative px-6 py-4 font-semibold font-satoshi transition-all whitespace-nowrap
              flex items-center gap-3 min-w-fit
              ${activeTab === 'configuration'
                ? 'text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }
            `}
            style={{
              background: activeTab === 'configuration'
                ? `linear-gradient(to right, ${PLAINFLOW_RED}, ${PLAINFLOW_RED_HOVER})`
                : 'transparent',
              borderBottom: activeTab === 'configuration' ? 'none' : '2px solid transparent',
            }}
          >
            <CloudArrowUpIcon className="w-6 h-6" />
            <div className="text-left">
              <div className="text-sm font-bold">Mapping Configuration</div>
              <div className={`text-xs ${activeTab === 'configuration' ? 'text-white text-opacity-90' : 'text-gray-500'}`}>
                Upload & Configure
              </div>
            </div>
            {activeTab === 'configuration' && (
              <div
                className="absolute bottom-0 left-0 right-0 h-1"
                style={{ background: PLAINFLOW_RED }}
              />
            )}
          </button>
          <button
            onClick={() => setActiveTab('mappings')}
            className={`
              relative px-6 py-4 font-semibold font-satoshi transition-all whitespace-nowrap
              flex items-center gap-3 min-w-fit
              ${activeTab === 'mappings'
                ? 'text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }
            `}
            style={{
              background: activeTab === 'mappings'
                ? `linear-gradient(to right, ${PLAINFLOW_RED}, ${PLAINFLOW_RED_HOVER})`
                : 'transparent',
              borderBottom: activeTab === 'mappings' ? 'none' : '2px solid transparent',
            }}
          >
            <DocumentTextIcon className="w-6 h-6" />
            <div className="text-left">
              <div className="text-sm font-bold">View Mappings</div>
              <div className={`text-xs ${activeTab === 'mappings' ? 'text-white text-opacity-90' : 'text-gray-500'}`}>
                {existingFinalTB.length > 0 ? `${existingFinalTB.length} File${existingFinalTB.length !== 1 ? 's' : ''}` : 'No Data'}
              </div>
            </div>
            {activeTab === 'mappings' && (
              <div
                className="absolute bottom-0 left-0 right-0 h-1"
                style={{ background: PLAINFLOW_RED }}
              />
            )}
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-b-lg border border-gray-200 shadow-sm">
        <div className="p-6">
          {activeTab === 'configuration' ? (
            <div className="space-y-6">
              {/* Configuration Tab Content */}
              
              {/* Loading State */}
              {isLoadingFiles && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    <p className="text-blue-700 font-satoshi">Checking for existing files...</p>
                  </div>
                </div>
              )}

              {/* Mapping Configuration Section */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900 font-satoshi">Upload Mapping Configuration</h2>
                  {existingMappingFiles.length > 0 && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded font-satoshi">
                      ✓ Current: {getFilename(existingMappingFiles[0])}
                    </span>
                  )}
                </div>

                {existingMappingFiles.length === 0 && (
                  <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800 font-satoshi">
                      <strong>⚠️ No mapping file found.</strong> Upload a mapping configuration file to proceed.
                    </p>
                  </div>
                )}

                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 bg-gray-50 hover:bg-gray-100 transition-colors">
                  <div className="flex flex-col items-center justify-center text-center">
                    <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mb-3" />
                    <p className="text-sm font-medium text-gray-700 mb-1 font-satoshi">
                      {existingMappingFiles.length > 0 ? 'Upload new file to replace existing' : 'Drag & drop files here, or click to select files'}
                    </p>
                    <p className="text-xs text-gray-500 mb-4 font-satoshi">
                      Accepted formats: .xlsx, .xls
                    </p>
                    <FileUpload
                      onFilesSelected={handleMappingFileSelect}
                      acceptedTypes={['.xlsx', '.xls']}
                      multiple={false}
                      maxFiles={1}
                    />
                  </div>
                </div>

                {uploadedMappingFile && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <DocumentTextIcon className="h-8 w-8 text-blue-600" />
                        <div>
                          <p className="text-sm font-medium text-gray-900 font-satoshi">{uploadedMappingFile.name}</p>
                          <p className="text-xs text-gray-600 font-satoshi">
                            {(uploadedMappingFile.size / 1024).toFixed(2)} KB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={handleUploadMapping}
                        disabled={uploadMappingMutation.isLoading}
                        className="flex items-center gap-2 px-4 py-2 rounded-md transition-all font-medium shadow-sm text-white font-satoshi disabled:opacity-50"
                        style={{
                          backgroundColor: uploadMappingMutation.isLoading ? '#9ca3af' : PLAINFLOW_RED,
                          cursor: uploadMappingMutation.isLoading ? 'not-allowed' : 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          if (!uploadMappingMutation.isLoading) {
                            e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER;
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!uploadMappingMutation.isLoading) {
                            e.currentTarget.style.backgroundColor = PLAINFLOW_RED;
                          }
                        }}
                      >
                        {uploadMappingMutation.isLoading ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            Uploading...
                          </>
                        ) : (
                          <>
                            <CloudArrowUpIcon className="h-5 w-5" />
                            Upload & Save
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* Current Config Files */}
                {existingMappingFiles.length > 0 && (
                  <div className="mt-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 font-satoshi">Current Config Files</h3>
                    <FileManager
                      files={existingMappingFiles}
                      folderType="config"
                      entity={getCompanyName()}
                      onDelete={refetchFiles}
                    />
                  </div>
                )}
              </div>

              {/* Category Mapping Report */}
              {!isLoadingFiles && existingFinalTB.length > 0 && (
                <div className="p-4 bg-green-50 border-2 border-green-300 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <CheckCircleIcon className="h-6 w-6 text-green-600" />
                      <div>
                        <h3 className="text-lg font-semibold text-green-900 font-satoshi">
                          Category Mapping Report
                        </h3>
                        <p className="text-sm text-green-700 font-satoshi">
                          {existingFinalTB.length} file(s) available • Ready to proceed to Step 5
                        </p>
                      </div>
                    </div>
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
            </div>
          ) : (
            <div className="space-y-6">
              {/* View Mappings Tab Content */}
              {existingFinalTB.length > 0 && finalTBSummary?.data ? (
                <FinalTBSummary
                  entity={getCompanyName()}
                  data={finalTBSummary.data}
                  currencyInfo={currencyInfo}
                  selectedCurrency={selectedCurrency}
                  fxRates={fxRates}
                />
              ) : (
                <div className="text-center py-12">
                  <DocumentTextIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2 font-satoshi">No Mapping Data Available</h3>
                  <p className="text-sm text-gray-500 font-satoshi">
                    Run category mapping to view the mapping results and analysis
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Re-run Category Mapping Section - Always visible at bottom */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 font-satoshi">
          Re-run Category Mapping
        </h2>

        {!canProceed && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800 font-satoshi">
              <strong>Required:</strong> Mapping file and adjusted trial balance (from Step 3)
            </p>
          </div>
        )}

        <button
          onClick={handleMapping}
          disabled={mappingMutation.isLoading || !canProceed}
          className="flex items-center gap-2 px-6 py-3 rounded-md transition-all font-medium shadow-sm text-white font-satoshi disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            backgroundColor: mappingMutation.isLoading || !canProceed ? '#9ca3af' : PLAINFLOW_RED,
            cursor: mappingMutation.isLoading || !canProceed ? 'not-allowed' : 'pointer'
          }}
          onMouseEnter={(e) => {
            if (!mappingMutation.isLoading && canProceed) {
              e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER;
            }
          }}
          onMouseLeave={(e) => {
            if (!mappingMutation.isLoading && canProceed) {
              e.currentTarget.style.backgroundColor = PLAINFLOW_RED;
            }
          }}
        >
          {mappingMutation.isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Mapping...
            </>
          ) : (
            <>
              <ArrowPathIcon className="h-5 w-5" />
              {existingFinalTB.length > 0 ? 'Re-run Category Mapping' : 'Execute Category Mapping'}
            </>
          )}
        </button>
      </div>

      {/* Mapping Results - Show when available */}
      {mappingResult && (
        <div className="card">
          {mappingResult.success && mappingResult.message && (
            <div className="mb-6 bg-green-50 border-2 border-green-300 rounded-lg p-4">
              <h2 className="text-xl font-bold text-green-800 text-center font-satoshi">{mappingResult.message}</h2>
            </div>
          )}

          <h2 className="text-lg font-semibold text-gray-900 mb-4 font-satoshi">📊 Mapping Results</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg text-center border-2 border-gray-200">
              <div className="text-2xl font-bold text-gray-900 font-satoshi">{mappingResult.mapping_summary?.total_records || 0}</div>
              <div className="text-sm text-gray-500 font-satoshi">Total GL Codes</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center border-2 border-green-300">
              <div className="text-2xl font-bold text-green-600 font-satoshi">{mappingResult.mapping_summary?.mapped_records || 0}</div>
              <div className="text-sm text-green-600 font-satoshi">Successfully Mapped</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center border-2 border-red-300">
              <div className="text-2xl font-bold text-red-600 font-satoshi">{mappingResult.mapping_summary?.unmapped_records || 0}</div>
              <div className="text-sm text-red-600 font-satoshi">Unmapped</div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg text-center border-2 border-blue-300">
              <div className="text-2xl font-bold text-blue-600 font-satoshi">{mappingResult.mapping_summary?.mapping_percentage || 0}%</div>
              <div className="text-sm text-blue-600 font-satoshi">Mapping Rate</div>
            </div>
          </div>

          {mappingResult.output_file && (
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 border-2 border-blue-300 rounded-lg p-6">
              <h3 className="text-lg font-bold text-blue-900 mb-3 font-satoshi">📄 Mapped Trial Balance Generated</h3>
              <p className="text-sm text-blue-700 mb-4 font-satoshi">
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
        </div>
      )}

      {/* Navigation - Always visible at bottom */}
      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/step3')}
            className="btn-secondary"
          >
            ← Back to Step 3
          </button>

          <button
            onClick={() => navigate('/step5')}
            className="btn-primary"
            disabled={!existingFinalTB.length && !mappingResult}
          >
            Continue to Step 5 →
          </button>
        </div>
      </div>
    </div>
  );
};

export default Step4CategoryMapping;
