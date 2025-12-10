import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  acceptedTypes?: string[];
  multiple?: boolean;
  maxFiles?: number;
  disabled?: boolean;
  className?: string;
}

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_LIGHT = 'rgb(255, 235, 238)';

const FileUpload: React.FC<FileUploadProps> = ({
  onFilesSelected,
  acceptedTypes = ['.xlsx', '.xls', '.xlsb'],
  multiple = true,
  maxFiles = 10,
  disabled = false,
  className = '',
}) => {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (disabled) return;

    const newFiles = [...uploadedFiles, ...acceptedFiles].slice(0, maxFiles);
    setUploadedFiles(newFiles);
    onFilesSelected(newFiles);
    
    toast.success(`${acceptedFiles.length} file(s) selected`);
  }, [uploadedFiles, onFilesSelected, maxFiles, disabled]);

  const removeFile = (index: number) => {
    const newFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(newFiles);
    onFilesSelected(newFiles);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.ms-excel.sheet.binary.macroEnabled.12': ['.xlsb'],
    },
    multiple,
    disabled,
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200
          ${disabled 
            ? 'opacity-50 cursor-not-allowed' 
            : 'hover:bg-gray-50'
          }
        `}
        style={{
          borderColor: isDragActive ? PLAINFLOW_RED : '#d1d5db',
          backgroundColor: isDragActive ? PLAINFLOW_RED_LIGHT : 'transparent'
        }}
      >
        <input {...getInputProps()} />
        <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
        <div className="mt-4">
          <p className="text-sm text-gray-600 font-satoshi">
            {isDragActive
              ? 'Drop the files here...'
              : 'Drag & drop files here, or click to select files'
            }
          </p>
          <p className="text-xs text-gray-500 mt-1 font-satoshi">
            Accepted formats: {acceptedTypes.join(', ')}
            {maxFiles > 1 && ` • Max ${maxFiles} files`}
          </p>
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-900 font-satoshi">
            Selected Files ({uploadedFiles.length})
          </h4>
          <div className="space-y-2">
            {uploadedFiles.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <DocumentIcon className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 font-satoshi">{file.name}</p>
                    <p className="text-xs text-gray-500 font-satoshi">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                {!disabled && (
                  <button
                    onClick={() => removeFile(index)}
                    className="text-gray-400 transition-colors duration-200"
                    style={{ color: '#9ca3af' }}
                    onMouseEnter={(e) => e.currentTarget.style.color = PLAINFLOW_RED}
                    onMouseLeave={(e) => e.currentTarget.style.color = '#9ca3af'}
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;