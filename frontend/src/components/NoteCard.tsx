// src/components/NoteCard.tsx

import React from 'react';
import { DocumentTextIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { GenerationStatusType } from '../types';

interface NoteCardProps {
  noteNumber: string;
  noteTitle: string;
  status: GenerationStatusType;
  onGenerate: (noteNumber: string) => void;
}

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';

const NoteCard: React.FC<NoteCardProps> = ({ 
  noteNumber, 
  noteTitle,
  status, 
  onGenerate 
}) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow h-full flex flex-col">
      {/* Header with title and status icon */}
      <div className="flex items-start justify-between gap-2 mb-4 flex-grow">
        <div className="flex items-start gap-2 flex-1 min-w-0">
          <DocumentTextIcon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: PLAINFLOW_RED }} />
          <h3 className="font-semibold text-gray-900 text-sm leading-tight font-satoshi">
            {noteTitle}
          </h3>
        </div>
        <div className="flex-shrink-0">
          {status === 'success' && (
            <CheckCircleIcon className="w-5 h-5 text-green-600" />
          )}
          {status === 'error' && (
            <XCircleIcon className="w-5 h-5 text-red-600" />
          )}
          {status === 'loading' && (
            <div 
              className="animate-spin rounded-full h-5 w-5 border-b-2" 
              style={{ borderColor: PLAINFLOW_RED }}
            ></div>
          )}
        </div>
      </div>
      
      <button
        onClick={() => onGenerate(noteNumber)}
        disabled={status === 'loading'}
        className="w-full py-2 px-4 rounded-md font-medium transition-all font-satoshi"
        style={{
          backgroundColor: status === 'loading' ? '#f3f4f6' : PLAINFLOW_RED,
          color: status === 'loading' ? '#9ca3af' : 'white',
          cursor: status === 'loading' ? 'not-allowed' : 'pointer'
        }}
        onMouseEnter={(e) => {
          if (status !== 'loading') {
            e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER;
          }
        }}
        onMouseLeave={(e) => {
          if (status !== 'loading') {
            e.currentTarget.style.backgroundColor = PLAINFLOW_RED;
          }
        }}
      >
        {status === 'loading' ? 'Generating...' : 'Generate Note'}
      </button>
    </div>
  );
};

export default NoteCard;