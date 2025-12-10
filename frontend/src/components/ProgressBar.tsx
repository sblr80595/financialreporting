import React from 'react';
import { CheckCircleIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface ProgressBarProps {
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message?: string;
  className?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  status,
  message,
  className = '',
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />;
      case 'processing':
        return <ClockIcon className="h-5 w-5 text-blue-600 animate-spin" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-600';
      case 'failed':
        return 'bg-red-600';
      case 'processing':
        return 'bg-blue-600';
      default:
        return 'bg-gray-300';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'processing':
        return 'Processing...';
      default:
        return 'Pending';
    }
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="text-sm font-medium text-gray-900">
            {getStatusText()}
          </span>
        </div>
        <span className="text-sm text-gray-500">{progress}%</span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${getStatusColor()}`}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>

      {message && (
        <p className="text-sm text-gray-600">{message}</p>
      )}
    </div>
  );
};

export default ProgressBar;
