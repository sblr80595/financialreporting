// src/components/BatchProgress.tsx

import React from 'react';
import { CheckCircleIcon, XCircleIcon, ClockIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { BatchStatus } from '../types';

interface BatchProgressProps {
  batchStatus: BatchStatus;
  onClose: () => void;
}

const BatchProgress: React.FC<BatchProgressProps> = ({ batchStatus, onClose }) => {
  const progress = batchStatus.total_notes > 0
    ? (batchStatus.completed_notes / batchStatus.total_notes) * 100
    : 0;

  const isComplete = batchStatus.status === 'completed' || batchStatus.status === 'failed';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">
            Batch Generation Progress
          </h2>
          {isComplete && (
            <button
              onClick={onClose}
              className="text-white hover:bg-blue-800 px-2 py-2 rounded-md transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          )}
        </div>
        
        {/* Content */}
        <div className="p-6">
          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                {batchStatus.completed_notes} of {batchStatus.total_notes} notes completed
              </span>
              <span className="text-sm font-medium text-gray-700">
                {Math.round(progress)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Current Note */}
          {batchStatus.current_note && (
            <div className="flex items-center gap-2 text-gray-600 mb-4 bg-blue-50 p-3 rounded-md">
              <ClockIcon className="w-4 h-4 animate-pulse text-blue-600" />
              <span className="text-sm">
                Currently generating Note {batchStatus.current_note}...
              </span>
            </div>
          )}

          {/* Results List */}
          <div className="max-h-64 overflow-y-auto space-y-2">
            {batchStatus.results.map((result, index) => (
              <div
                key={index}
                className={`flex items-center gap-3 p-3 rounded-md ${
                  result.success ? 'bg-green-50' : 'bg-red-50'
                }`}
              >
                {result.success ? (
                  <CheckCircleIcon className="w-5 h-5 text-green-600 flex-shrink-0" />
                ) : (
                  <XCircleIcon className="w-5 h-5 text-red-600 flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    Note {result.note_number}
                  </p>
                  <p className="text-xs text-gray-600 truncate">
                    {result.message}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Close Button */}
          {isComplete && (
            <button
              onClick={onClose}
              className="w-full mt-6 bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
            >
              {batchStatus.status === 'completed' ? 'Done' : 'Close'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default BatchProgress;
