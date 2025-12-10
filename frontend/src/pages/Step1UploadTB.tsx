import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from 'react-query';
import { 
  CloudArrowUpIcon, 
  CheckCircleIcon, 
  ArrowRightIcon, 
  CloudArrowDownIcon,
  ExclamationCircleIcon,
  EyeIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import FileUpload from '../components/FileUpload';
import FileManager from '../components/FileManager';
import { apiService } from '../services/api';
import { useEntity } from '../contexts/EntityContext';

const Step1UploadTB: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [selectedOption, setSelectedOption] = useState<'sap' | 'upload'>('upload');
  const [showPreview, setShowPreview] = useState(false);
  const [checkConnectivity, setCheckConnectivity] = useState(false);

  // Check SAP connectivity - only when button is clicked
  const { data: sapConnectivity, isLoading: isCheckingSAP, refetch: recheckSAP } = useQuery(
    ['sap-connectivity', getCompanyName()],
    () => apiService.checkSAPConnectivity(getCompanyName()),
    {
      enabled: checkConnectivity, // Only run when checkConnectivity is true
      staleTime: 5 * 60 * 1000, // Cache for 5 minutes
      onSuccess: (response) => {
        console.log('[SAP] Connectivity check:', response.data);
      },
      onError: (error) => {
        console.error('[SAP] Connectivity check failed:', error);
      }
    }
  );

  // Check for existing files - AUTO-FETCH on mount
  const { data: filesData, refetch: refetchFiles, isLoading: isLoadingFiles } = useQuery(
    ['entity-files', getCompanyName()],
    () => apiService.listEntityFiles(getCompanyName()),
    {
      enabled: true, // Auto-fetch on mount
      refetchOnMount: 'always', // Always refetch when component mounts
      staleTime: 0, // Always consider data stale to ensure refetch
      cacheTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
      onSuccess: (response) => {
        const files = response.data?.unadjusted_trialbalance || [];
        console.log('[Step 1] Existing TB files found:', files);
      },
      onError: (error) => {
        console.error('[Step 1] Error loading files:', error);
      }
    }
  );

  // Get existing files from query data
  const existingFiles = filesData?.data?.unadjusted_trialbalance || [];
  const sapAvailable = sapConnectivity?.data?.available || false;
  const sapMessage = sapConnectivity?.data?.message || '';

  // SAP extraction mutation
  const sapExtractionMutation = useMutation(
    () => apiService.extractTrialBalanceFromSAP(getCompanyName()),
    {
      onSuccess: (response) => {
        toast.success('Trial balance extracted from SAP successfully!');
        refetchFiles(); // Refresh file list
        setShowPreview(true);
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'SAP extraction failed');
      },
    }
  );

  const uploadMutation = useMutation(
    (data: { entity: string; file: File }) => 
      apiService.uploadTrialBalance(data.entity, data.file),
    {
      onSuccess: (response) => {
        toast.success('Trial balance uploaded successfully!');
        refetchFiles(); // Refresh file list
        navigate('/step2');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Upload failed');
      },
    }
  );

  const handleFileSelect = (files: File[]) => {
    if (files.length > 0) {
      setUploadedFile(files[0]);
    }
  };

  const handleUpload = () => {
    if (!uploadedFile) {
      toast.error('Please select a file first');
      return;
    }

    uploadMutation.mutate({
      entity: getCompanyName(),
      file: uploadedFile,
    });
  };

  const handleSkipToNext = () => {
    toast.success('Using existing trial balance file');
    navigate('/step2');
  };

  const handleSAPExtract = () => {
    if (!sapAvailable) {
      toast.error('SAP connection is not available');
      return;
    }
    sapExtractionMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Option Selection - Top Section */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Select Trial Balance Source
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Option 1: SAP/ERP Extraction */}
          <div
            className={`relative border-2 rounded-lg p-6 cursor-pointer transition-all ${
              selectedOption === 'sap'
                ? 'border-blue-500 bg-blue-50'
                : sapAvailable
                ? 'border-gray-300 hover:border-blue-300'
                : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
            }`}
            onClick={() => sapAvailable && setSelectedOption('sap')}
          >
            <div className="flex items-start space-x-3">
              <div className={`flex-shrink-0 ${sapAvailable ? 'text-blue-600' : 'text-gray-400'}`}>
                <CloudArrowDownIcon className="h-8 w-8" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Extract from SAP/ERP
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Automatically pull trial balance data from your entity's ERP system
                </p>
                
                {!checkConnectivity ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setCheckConnectivity(true);
                    }}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Check SAP Connectivity
                  </button>
                ) : isCheckingSAP ? (
                  <div className="flex items-center text-sm text-gray-500">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                    Checking connectivity...
                  </div>
                ) : sapAvailable ? (
                  <div className="flex items-center text-sm text-green-600">
                    <CheckCircleIcon className="h-4 w-4 mr-1" />
                    {sapConnectivity?.data?.entity_name || 'SAP Connection Available'}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center text-sm text-orange-600">
                      <ExclamationCircleIcon className="h-4 w-4 mr-1" />
                      {sapMessage}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        recheckSAP();
                      }}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Retry Connection
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            {selectedOption === 'sap' && sapAvailable && (
              <div className="mt-4 pt-4 border-t border-blue-200">
                <button
                  onClick={handleSAPExtract}
                  disabled={sapExtractionMutation.isLoading}
                  className="btn-primary w-full"
                >
                  {sapExtractionMutation.isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Extracting from SAP...
                    </>
                  ) : (
                    <>
                      <CloudArrowDownIcon className="h-5 w-5 mr-2" />
                      Extract Trial Balance
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Option 2: Manual Upload */}
          <div
            className={`relative border-2 rounded-lg p-6 cursor-pointer transition-all ${
              selectedOption === 'upload'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-blue-300'
            }`}
            onClick={() => setSelectedOption('upload')}
          >
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 text-blue-600">
                <CloudArrowUpIcon className="h-8 w-8" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Upload Excel File
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Manually upload trial balance data from an Excel file
                </p>
                <div className="flex items-center text-sm text-green-600">
                  <CheckCircleIcon className="h-4 w-4 mr-1" />
                  Always Available
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Existing Data - Compact Display */}
      {!isLoadingFiles && existingFiles.length > 0 && (
        <div className="card bg-green-50 border-2 border-green-300">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <div>
                <h3 className="text-lg font-semibold text-green-900">
                  Trial Balance Data Available
                </h3>
                <p className="text-sm text-green-700">
                  {existingFiles.length} file(s) ready • Ready to proceed to Step 2
                </p>
              </div>
            </div>
            <button
              onClick={handleSkipToNext}
              className="btn-primary bg-green-600 hover:bg-green-700 flex items-center space-x-2"
            >
              <span>Continue to Step 2</span>
              <ArrowRightIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      {/* Upload Section - Only shown when 'upload' is selected */}
      {selectedOption === 'upload' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {existingFiles.length > 0 ? 'Upload New File (Replace Existing)' : 'Upload Trial Balance'}
          </h2>
          
          <FileUpload
            onFilesSelected={handleFileSelect}
            acceptedTypes={['.xlsx', '.xls']}
            multiple={false}
            maxFiles={1}
          />
          
          {uploadedFile && (
            <div className="mt-4 p-4 bg-gray-50 rounded border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{uploadedFile.name}</p>
                  <p className="text-xs text-gray-600">
                    {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={handleUpload}
                  disabled={uploadMutation.isLoading}
                  className="btn-primary"
                >
                  {uploadMutation.isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <CloudArrowUpIcon className="h-5 w-5 mr-2" />
                      Upload & Continue
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Trial Balance Data Preview/Download Section */}
      {existingFiles.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <DocumentTextIcon className="h-6 w-6 mr-2 text-blue-600" />
              Trial Balance Files
            </h2>
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
            >
              <EyeIcon className="h-4 w-4 mr-1" />
              {showPreview ? 'Hide' : 'Show'} Files
            </button>
          </div>

          {showPreview && (
            <div className="bg-white rounded border border-gray-200">
              <FileManager 
                files={existingFiles}
                folderType="unadjusted_trialbalance"
                entity={getCompanyName()}
                onDelete={refetchFiles}
              />
            </div>
          )}

          {!showPreview && (
            <div className="text-sm text-gray-600">
              Click "Show Files" to view and download trial balance data
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Step1UploadTB;
