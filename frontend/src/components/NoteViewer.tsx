// src/components/NoteViewer.tsx

import React, { useState, useEffect } from 'react';
import { DocumentTextIcon, XMarkIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { renderMarkdown } from '../utils/markdown';
import toast from 'react-hot-toast';

interface NoteViewerProps {
  companyName: string;
  filename: string;
  noteNumber: string | null;
  title: string | null;
  onClose: () => void;
}

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';

const NoteViewer: React.FC<NoteViewerProps> = ({ 
  companyName, 
  filename, 
  noteNumber,
  title,
  onClose 
}) => {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContent = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiService.getNoteContent(companyName, filename);
        setContent(response.content);
      } catch (err) {
        console.error('Error fetching note content:', err);
        setError('Failed to load note content');
        toast.error('Failed to load note content');
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [companyName, filename]);

  const handleDownload = async () => {
    try {
      await apiService.triggerNoteDownload(companyName, filename);
      toast.success('Note downloaded successfully');
    } catch (err) {
      toast.error('Failed to download note');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 flex items-center justify-between" style={{ background: `linear-gradient(to right, ${PLAINFLOW_RED}, ${PLAINFLOW_RED_HOVER})` }}>
          <div className="flex items-center gap-3">
            <DocumentTextIcon className="w-6 h-6 text-white" />
            <div>
              <h2 className="text-xl font-bold text-white font-satoshi">
                {title || (noteNumber ? `Note ${noteNumber}` : 'Generated Note')}
              </h2>
              {noteNumber && title && (
                <p className="text-white text-opacity-90 text-sm font-satoshi">
                  Note {noteNumber}
                </p>
              )}
              {!title && (
                <p className="text-white text-opacity-90 text-sm font-satoshi">
                  {filename}
                </p>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 bg-white px-4 py-2 rounded-md transition-all font-medium font-satoshi"
              style={{ color: PLAINFLOW_RED }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgb(255, 235, 238)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              Download
            </button>
            <button
              onClick={onClose}
              className="text-white px-3 py-2 rounded-md transition-colors"
              style={{ backgroundColor: 'transparent' }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-auto p-6 bg-gray-50">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: PLAINFLOW_RED }}></div>
              <span className="ml-3 text-gray-600 font-satoshi">Loading note...</span>
            </div>
          )}
          
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <p className="text-red-800 font-satoshi">{error}</p>
            </div>
          )}
          
          {!loading && !error && content && (
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <div 
                className="prose prose-sm max-w-none font-satoshi"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NoteViewer;
