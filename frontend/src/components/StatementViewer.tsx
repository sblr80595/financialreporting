// src/components/StatementViewer.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { XMarkIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import * as XLSX from 'xlsx';

interface StatementViewerProps {
  filename: string;
  companyName: string;
  statementType: 'pl' | 'bs' | 'cf';
  onClose: () => void;
}

const PLAINFLOW_RED = 'rgb(139, 0, 16)';

const StatementViewer: React.FC<StatementViewerProps> = ({
  filename,
  companyName,
  statementType,
  onClose,
}) => {
  const [tableData, setTableData] = useState<any[][]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadExcelData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch the Excel file
      const endpoint = statementType === 'pl' 
        ? `/api/pl-statement/${companyName}/download/${filename}`
        : statementType === 'bs'
        ? `/api/bs-statement/${companyName}/download/${filename}`
        : `/api/cashflow-statement/${companyName}/download/${filename}`;

      const response = await fetch(endpoint);
      if (!response.ok) throw new Error('Failed to load statement');

      const arrayBuffer = await response.arrayBuffer();
      const workbook = XLSX.read(arrayBuffer, { type: 'array' });

      // Get the first sheet
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];

      // Convert to array of arrays
      const data = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' });
      setTableData(data as any[][]);
    } catch (err: any) {
      console.error('Error loading Excel:', err);
      setError(err.message || 'Failed to load statement');
    } finally {
      setLoading(false);
    }
  }, [filename, companyName, statementType]);

  useEffect(() => {
    loadExcelData();
  }, [loadExcelData]);

  const handleDownload = () => {
    const endpoint = statementType === 'pl' 
      ? `/api/pl-statement/${companyName}/download/${filename}`
      : statementType === 'bs'
      ? `/api/bs-statement/${companyName}/download/${filename}`
      : `/api/cashflow-statement/${companyName}/download/${filename}`;

    const link = document.createElement('a');
    link.href = endpoint;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getStatementTitle = () => {
    if (statementType === 'pl') return 'Profit & Loss Statement';
    if (statementType === 'bs') return 'Balance Sheet';
    return 'Cash Flow Statement';
  };

  const formatCellValue = (value: any, rowIndex: number, colIndex: number) => {
    if (value === null || value === undefined || value === '') return '';
    
    // Check if it's a number and format it
    if (typeof value === 'number') {
      // Check if it's in the amount column (usually last column for financial statements)
      if (colIndex === tableData[rowIndex]?.length - 1 || colIndex === tableData[rowIndex]?.length - 2) {
        return new Intl.NumberFormat('en-IN', {
          minimumFractionDigits: 0,
          maximumFractionDigits: 2,
        }).format(value);
      }
      return value.toString();
    }
    
    return value.toString();
  };

  const isTotalRow = (row: any[]) => {
    const firstCell = row[0]?.toString().toLowerCase() || '';
    return firstCell.includes('total') || firstCell.includes('net profit') || firstCell.includes('net loss');
  };

  const isHeaderRow = (rowIndex: number) => {
    // Company name, statement title, date rows are usually in the first few rows
    return rowIndex < 4;
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
          className="p-4 border-b flex items-center justify-between"
          style={{ backgroundColor: PLAINFLOW_RED }}
        >
          <div>
            <h2 className="text-xl font-bold text-white font-satoshi">
              {getStatementTitle()}
            </h2>
            <p className="text-sm text-white text-opacity-90 font-satoshi">
              {companyName.toUpperCase()} • {filename}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-100 flex items-center gap-2 font-satoshi font-semibold transition-colors"
            >
              <ArrowDownTrayIcon className="w-5 h-5" />
              Download Excel
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-6 h-6 text-white" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: PLAINFLOW_RED }}></div>
              <span className="ml-3 text-gray-600 font-satoshi">Loading statement...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <p className="text-red-700 font-satoshi">{error}</p>
            </div>
          )}

          {!loading && !error && tableData.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <tbody>
                  {tableData.map((row, rowIndex) => (
                    <tr 
                      key={rowIndex}
                      className={`
                        ${isHeaderRow(rowIndex) ? 'bg-gray-50' : ''}
                        ${isTotalRow(row) ? 'font-bold border-t-2 border-b-2 border-gray-400' : ''}
                      `}
                    >
                      {row.map((cell, colIndex) => (
                        <td
                          key={colIndex}
                          className={`
                            px-4 py-2 border-b border-gray-200 font-satoshi
                            ${colIndex === 0 ? 'text-left' : 'text-right'}
                            ${isHeaderRow(rowIndex) ? 'font-semibold text-center' : ''}
                            ${isTotalRow(row) ? 'font-bold' : ''}
                          `}
                          style={{
                            fontSize: isHeaderRow(rowIndex) ? '1.1em' : '0.95em',
                            ...(isHeaderRow(rowIndex) && rowIndex === 0 ? { fontSize: '1.3em' } : {})
                          }}
                        >
                          {formatCellValue(cell, rowIndex, colIndex)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <p className="text-xs text-gray-600 text-center font-satoshi">
            View-only mode • Download to edit or save
          </p>
        </div>
      </div>
    </div>
  );
};

export default StatementViewer;
