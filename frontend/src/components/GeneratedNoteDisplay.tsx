// src/components/GeneratedNoteDisplay.tsx

import React, { useState, useEffect } from 'react';
import { XMarkIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { GenerationResponse } from '../types';
import { parseMarkdownTables, downloadAsExcel, formatNoteFileName, TableData } from '../utils/noteTableUtils';
import { useEntity } from '../contexts/EntityContext';
import toast from 'react-hot-toast';

interface GeneratedNoteDisplayProps {
  note: GenerationResponse;
  onClose: () => void;
}

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';

const GeneratedNoteDisplay: React.FC<GeneratedNoteDisplayProps> = ({ note, onClose }) => {
  const { getCompanyName } = useEntity();
  const companyName = getCompanyName();
  const [tables, setTables] = useState<TableData[]>([]);

  useEffect(() => {
    // Parse markdown content to extract tables
    if (note.content) {
      const extractedTables = parseMarkdownTables(note.content);
      setTables(extractedTables);
    }
  }, [note.content]);

  const handleDownload = () => {
    if (tables.length === 0) {
      toast.error('No tables found in note to export');
      return;
    }

    // Extract note title from output_file or use note number
    const noteTitle = note.output_file?.split('\\').pop()?.replace(/\.(md|txt)$/i, '') || '';
    const filename = formatNoteFileName(note.note_number || '', noteTitle, companyName);
    
    const sheetNames = tables.map((_, index) => 
      noteTitle ? `${noteTitle.substring(0, 25)}_${index + 1}` : `Note_${note.note_number}_${index + 1}`
    );
    
    downloadAsExcel(tables, filename, sheetNames);
    toast.success('Note downloaded as Excel successfully');
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div 
          className="px-6 py-4 flex items-center justify-between" 
          style={{ background: `linear-gradient(to right, ${PLAINFLOW_RED}, ${PLAINFLOW_RED_HOVER})` }}
        >
          <div>
            <h2 className="text-xl font-bold text-white font-satoshi">
              Note {note.note_number}
            </h2>
            <p className="text-white text-opacity-90 text-sm font-satoshi mt-1">
              {note.output_file?.split('\\').pop() || 'Generated Note'}
            </p>
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
              Download Excel
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
        
        {/* Content - Scrollable Tables */}
        <div className="flex-1 overflow-auto p-6 bg-gray-50">
          {tables.length === 0 ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
              <p className="text-yellow-800 font-satoshi">
                No tables found in this note. The note content may not be in tabular format.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {tables.map((table, tableIndex) => (
                <div key={tableIndex} className="bg-white rounded-lg shadow-sm overflow-hidden">
                  {tables.length > 1 && (
                    <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
                      <h3 className="text-sm font-semibold text-gray-700 font-satoshi">
                        Table {tableIndex + 1}
                      </h3>
                    </div>
                  )}
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {table.headers.map((header, index) => (
                            <th
                              key={index}
                              className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider font-satoshi"
                              style={{ backgroundColor: 'rgb(249, 250, 251)' }}
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {table.rows.map((row, rowIndex) => (
                          <tr 
                            key={rowIndex}
                            className="hover:bg-gray-50 transition-colors"
                          >
                            {row.map((cell, cellIndex) => (
                              <td
                                key={cellIndex}
                                className="px-4 py-3 text-sm text-gray-900 font-satoshi whitespace-nowrap"
                              >
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Footer Info */}
        <div className="px-6 py-3 bg-gray-100 border-t border-gray-200">
          <p className="text-xs text-gray-600 font-satoshi">
            {tables.length > 0 ? (
              <>
                Showing {tables.length} table{tables.length > 1 ? 's' : ''} • 
                Click "Download Excel" to export in formatted Excel format
              </>
            ) : (
              'No tabular data available for display'
            )}
          </p>
        </div>
      </div>
    </div>
  );
};

export default GeneratedNoteDisplay;