import React, { useState } from 'react';
import { 
  DocumentTextIcon, 
  TrashIcon, 
  ArrowDownTrayIcon,
  EyeIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';

interface FileInfo {
  filename: string;
  file_size: number;
  created_at: string;
  modified_at: string;
}

interface FileManagerProps {
  files: (string | FileInfo)[];
  folderType: string;
  entity: string;
  onDelete?: () => void;
  showActions?: boolean;
}

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_LIGHT = 'rgb(255, 235, 238)';

const FileManager: React.FC<FileManagerProps> = ({ 
  files, 
  folderType, 
  entity, 
  onDelete,
  showActions = true 
}) => {
  const [deletingFile, setDeletingFile] = useState<string | null>(null);
  const [previewFile, setPreviewFile] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const handleDownload = async (filename: string) => {
    try {
      toast.loading('Downloading file...');
      
      let response;
      // Use different API endpoints based on folder type
      if (folderType === 'adjusted_trialbalance') {
        response = await apiService.downloadAdjustmentFile(entity, filename);
      } else {
        response = await apiService.downloadEntityFile(entity, folderType, filename);
      }
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.dismiss();
      toast.success('File downloaded successfully');
    } catch (error) {
      toast.dismiss();
      toast.error('Download failed');
    }
  };

  const handleDelete = async (filename: string) => {
    if (!window.confirm(`Are you sure you want to delete ${filename}?`)) {
      return;
    }

    try {
      setDeletingFile(filename);
      await apiService.deleteFile(entity, folderType, filename);
      toast.success('File deleted successfully');
      onDelete?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Delete failed');
    } finally {
      setDeletingFile(null);
    }
  };

  const handleView = async (filename: string) => {
    setPreviewFile(filename);
    setLoadingPreview(true);
    setPreviewData(null);
    
    try {
      let response;
      
      // Use different API endpoints based on folder type
      if (folderType === 'adjusted_trialbalance') {
        // Use the working adjustments API
        response = await apiService.previewAdjustmentFile(entity, filename);
        // Convert the data format to match our expected format
        const data = response.data;
        setPreviewData({
          filename: data.filename,
          total_rows: data.total_rows,
          total_columns: data.total_columns,
          columns: data.columns,
          rows: data.data?.map((row: any) => data.columns.map((col: string) => row[col])) || []
        });
      } else {
        // Use generic file preview API for other folder types
        response = await apiService.previewFile(entity, folderType, filename);
        setPreviewData(response.data);
      }
    } catch (error: any) {
      console.error('Failed to load file preview:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load file preview';
      toast.error(errorMessage);
      setPreviewFile(null); // Close modal on error
    } finally {
      setLoadingPreview(false);
    }
  };

  const closePreview = () => {
    setPreviewFile(null);
    setPreviewData(null);
    setLoadingPreview(false);
  };

  if (files.length === 0) {
    return null;
  }

  return (
    <>
      <div className="space-y-2">
        {files.map((file, idx) => {
          // Handle both string filenames and file objects
          const filename = typeof file === 'string' ? file : file.filename;
          const fileSize = typeof file === 'string' ? null : file.file_size;
          
          return (
          <div 
            key={idx} 
            className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
          >
            <div className="flex items-center space-x-3 flex-1 min-w-0">
              <DocumentTextIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate font-satoshi">
                  {filename}
                </p>
                <p className="text-xs text-gray-500 font-satoshi">
                  {folderType.replace(/_/g, ' ')}
                  {fileSize && ` • ${(fileSize / 1024).toFixed(2)} KB`}
                </p>
              </div>
            </div>
            
            {showActions && (
              <div className="flex items-center space-x-2 ml-4">
                <button
                  onClick={() => handleView(filename)}
                  className="p-1.5 rounded transition-all font-satoshi"
                  style={{ color: PLAINFLOW_RED }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = PLAINFLOW_RED_LIGHT}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  title="View details"
                >
                  <EyeIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDownload(filename)}
                  className="p-1.5 text-green-600 hover:bg-green-50 rounded transition-colors font-satoshi"
                  title="Download"
                >
                  <ArrowDownTrayIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(filename)}
                  disabled={deletingFile === filename}
                  className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50 font-satoshi"
                  title="Delete"
                >
                  {deletingFile === filename ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                  ) : (
                    <TrashIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
            )}
          </div>
          );
        })}
      </div>

      {/* File Preview Modal */}
      {previewFile && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={closePreview}
        >
          <div 
            className="bg-white rounded-lg shadow-xl w-full max-w-7xl max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="px-6 py-4 flex items-center justify-between bg-gradient-to-r from-[rgb(139,0,16)] to-[rgb(110,0,13)]">
              <div>
                <h2 className="text-xl font-bold text-white font-satoshi">
                  {previewFile}
                </h2>
                {previewData && previewData.total_rows !== undefined && (
                  <p className="text-white text-opacity-90 text-sm font-satoshi mt-1">
                    {previewData.total_rows.toLocaleString()} rows × {previewData.total_columns} columns
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleDownload(previewFile)}
                  className="flex items-center gap-2 bg-white px-4 py-2 rounded-md transition-all font-medium font-satoshi text-[rgb(139,0,16)] hover:bg-red-50"
                >
                  <ArrowDownTrayIcon className="w-4 h-4" />
                  Download
                </button>
                <button
                  onClick={closePreview}
                  className="text-white px-3 py-2 rounded-md transition-colors hover:bg-[rgb(110,0,13)]"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            {/* Content - Scrollable Table */}
            <div className="flex-1 overflow-auto p-6 bg-gray-50">
              {loadingPreview ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-gray-500 font-satoshi">Loading preview...</div>
                </div>
              ) : previewData ? (
                <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {previewData.columns?.map((col: string, idx: number) => (
                            <th
                              key={idx}
                              className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider font-satoshi whitespace-nowrap"
                              style={{ backgroundColor: 'rgb(249, 250, 251)' }}
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {previewData.rows?.map((row: any[], rowIdx: number) => (
                          <tr key={rowIdx} className="hover:bg-gray-50 transition-colors">
                            {row.map((cell: any, cellIdx: number) => (
                              <td
                                key={cellIdx}
                                className="px-4 py-3 text-sm text-gray-900 font-satoshi whitespace-nowrap"
                              >
                                {cell !== null && cell !== undefined ? String(cell) : ''}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64">
                  <div className="text-red-500 font-satoshi">Failed to load preview</div>
                </div>
              )}
            </div>
            
            {/* Footer Info */}
            {previewData && previewData.rows && previewData.total_rows !== undefined && previewData.total_rows > previewData.rows.length && (
              <div className="px-6 py-3 bg-gray-100 border-t border-gray-200">
                <p className="text-xs text-gray-600 font-satoshi">
                  Showing first {previewData.rows.length.toLocaleString()} of {previewData.total_rows.toLocaleString()} rows
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default FileManager;