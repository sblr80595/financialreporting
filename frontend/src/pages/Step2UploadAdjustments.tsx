import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from 'react-query';
import { 
  CheckCircleIcon,
  ArrowRightIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import FileUpload from '../components/FileUpload';
import FileManager from '../components/FileManager';
import { apiService } from '../services/api';
import { useEntity } from '../contexts/EntityContext';

const Step2UploadAdjustments: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  // Check for existing files - AUTO FETCH on mount
  const { data: filesData, refetch: refetchFiles, isLoading: isLoadingFiles } = useQuery(
    ['entity-files', getCompanyName()],
    () => apiService.listEntityFiles(getCompanyName()),
    {
      enabled: true, // Auto-fetch on mount
      refetchOnMount: 'always', // Always refetch when component mounts
      refetchOnWindowFocus: false,
      staleTime: 0, // Always consider data stale to ensure refetch
      cacheTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
      onSuccess: (response) => {
        console.log('[Step 2] Full API response:', response);
        console.log('[Step 2] Response data:', response.data);
        const files = response.data?.manual_adjustments || [];
        console.log('[Step 2] Existing adjustment files:', files);
      },
      onError: (error) => {
        console.error('[Step 2] Error fetching files:', error);
      }
    }
  );

  // Get existing files from query data
  const existingFiles = filesData?.data?.manual_adjustments || [];

  const uploadMutation = useMutation(
    (data: { entity: string; files: File[] }) => 
      apiService.uploadAdjustments(data.entity, data.files),
    {
      onSuccess: (response) => {
        toast.success('Adjustment files uploaded successfully!');
        refetchFiles(); // Refresh file list
        navigate('/step3');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Upload failed');
      },
    }
  );

  const handleFileSelect = (files: File[]) => {
    setUploadedFiles(files);
  };

  const handleUpload = () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please select files first');
      return;
    }

    uploadMutation.mutate({
      entity: getCompanyName(),
      files: uploadedFiles,
    });
  };

  const handleSkipToNext = () => {
    toast.success('Using existing adjustment files');
    navigate('/step3');
  };

  return (
    <div className="space-y-6">
      {/* Loading State */}
      {isLoadingFiles && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <p className="text-blue-700">Checking for existing files...</p>
          </div>
        </div>
      )}

      {/* Existing Data - Simple & Clean */}
      {!isLoadingFiles && existingFiles.length > 0 && (
        <div className="card bg-green-50 border-2 border-green-300">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <div>
                <h3 className="text-lg font-semibold text-green-900">
                  Adjustment Files Already Uploaded
                </h3>
                <p className="text-sm text-green-700">
                  {existingFiles.length} file(s) available • Ready to proceed to Step 3
                </p>
              </div>
            </div>
            <button
              onClick={handleSkipToNext}
              className="btn-primary bg-green-600 hover:bg-green-700 flex items-center space-x-2"
            >
              <span>Continue to Step 3</span>
              <ArrowRightIcon className="h-5 w-5" />
            </button>
          </div>
          
          {/* File List with Download */}
          <div className="bg-white rounded border border-green-200 p-4">
            <FileManager 
              files={existingFiles}
              folderType="manual_adjustments"
              entity={getCompanyName()}
              onDelete={refetchFiles}
            />
          </div>
        </div>
      )}

      {/* Upload Adjustment Files - Simple Execution */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {existingFiles.length > 0 ? 'Upload New Files (Replace Existing)' : 'Upload Adjustment Files'}
        </h2>
        
        <FileUpload
          onFilesSelected={handleFileSelect}
          acceptedTypes={['.xlsx', '.xls']}
          multiple={true}
          maxFiles={10}
        />
        
        {uploadedFiles.length > 0 && (
          <div className="mt-4 p-4 bg-gray-50 rounded border border-gray-200">
            <p className="text-sm font-medium text-gray-900 mb-2">
              {uploadedFiles.length} file(s) selected
            </p>
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
        )}
      </div>

      {/* Navigation */}
      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/step1')}
            className="btn-secondary"
          >
            ← Back to Step 1
          </button>
          
          {existingFiles.length > 0 && (
            <button
              onClick={() => navigate('/step3')}
              className="btn-primary"
            >
              Continue to Step 3 →
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Step2UploadAdjustments;
