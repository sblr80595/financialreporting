// FILE: src/components/BalanceSheetGenerator.tsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  DocumentTextIcon,
  ArrowDownTrayIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ExclamationTriangleIcon,
  ArrowPathIcon,
  TrashIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { balanceSheetApi, StatementReadinessResponse } from '../services/api';
import StatementViewer from './StatementViewer';
import { usePeriod } from '../contexts/PeriodContext';

interface BalanceSheetFile {
  filename: string;
  file_path: string;
  size_bytes: number;
  generated_at: string;
  download_url: string;
}

interface BalanceSheetGeneratorProps {
  entity: string;
  defaultDate?: string;
}

// Plainflow Red theme colors (matching P&L)
const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';
const PLAINFLOW_RED_LIGHT = 'rgb(255, 235, 238)';

const BalanceSheetGenerator: React.FC<BalanceSheetGeneratorProps> = ({ 
  entity,
  defaultDate = '31 March 2025'
}) => {
  const { currentPeriodColumn } = usePeriod();
  const [asAtDate, setAsAtDate] = useState<string>(currentPeriodColumn || defaultDate);
  const [readiness, setReadiness] = useState<StatementReadinessResponse | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastGenerated, setLastGenerated] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [countdown, setCountdown] = useState(10);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const countdownRef = useRef<NodeJS.Timeout | null>(null);
  const [bsStatements, setBsStatements] = useState<BalanceSheetFile[]>([]);
  const [loadingStatements, setLoadingStatements] = useState(true);
  const [viewingStatement, setViewingStatement] = useState<string | null>(null);

  // Update date when context changes
  useEffect(() => {
    if (currentPeriodColumn) {
      setAsAtDate(currentPeriodColumn);
    }
  }, [currentPeriodColumn]);

  // Fetch existing Balance Sheet statements
  const fetchBSStatements = useCallback(async () => {
    try {
      setLoadingStatements(true);
      const response = await balanceSheetApi.listBalanceSheets(entity, entity);
      setBsStatements(response.statements || []);
      console.log('[BalanceSheet] Found existing Balance Sheet statements:', response.statements?.length);
    } catch (err) {
      console.error('Error loading Balance Sheet statements:', err);
      setBsStatements([]);
    } finally {
      setLoadingStatements(false);
    }
  }, [entity]);

  // Check readiness function
  const checkReadiness = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await balanceSheetApi.checkReadiness(entity, entity);
      setReadiness(response);
      setCountdown(10);
    } catch (err: any) {
      setError('Failed to check statement readiness');
      console.error('Readiness check error:', err);
    } finally {
      setLoading(false);
    }
  }, [entity]);

  // Load data on mount and when entity changes
  useEffect(() => {
    checkReadiness();
    fetchBSStatements();
  }, [entity, checkReadiness, fetchBSStatements]);

  // AUTO-REFRESH LOGIC
  useEffect(() => {
    // Clear existing intervals
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (countdownRef.current) clearInterval(countdownRef.current);

    // Only auto-refresh if not all notes are ready and auto-refresh is enabled
    if (autoRefresh && readiness && !readiness.is_ready) {
      // Main refresh interval (every 10 seconds)
      intervalRef.current = setInterval(() => {
        checkReadiness();
        setCountdown(10);
      }, 10000);

      // Countdown timer (every second)
      countdownRef.current = setInterval(() => {
        setCountdown((prev) => (prev > 0 ? prev - 1 : 10));
      }, 1000);
    }

    // Cleanup
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [autoRefresh, readiness, checkReadiness]);

  // Generate Balance Sheet
  const handleGenerate = async () => {
    if (!readiness || !readiness.is_ready) {
      setError('Not all required notes are available. Please generate missing notes first.');
      return;
    }

  setGenerating(true);
  setError(null);

    try {
      const response = await balanceSheetApi.generateBalanceSheet({
        company_name: entity,
        as_at_date: asAtDate,
        cpm_category: entity
      });

      if (response.success) {
        // mark time of generation
        setLastGenerated(new Date().toISOString());
        toast.success('Balance Sheet generated successfully!');
        // Refresh the list to show the new file
        fetchBSStatements();
      } else {
        setError(response.message);
        toast.error(response.message || 'Failed to generate Balance Sheet');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate Balance Sheet');
      toast.error('Failed to generate Balance Sheet');
      console.error('Generation error:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (filename: string) => {
    if (!window.confirm(`Are you sure you want to delete ${filename}?`)) {
      return;
    }

    try {
      console.log('[BalanceSheet] Deleting statement:', filename, 'for entity:', entity);
      const response = await balanceSheetApi.deleteBalanceSheet(entity, filename);
      console.log('[BalanceSheet] Delete response:', response);
      toast.success('Statement deleted successfully');
      // Refresh the list
      await fetchBSStatements();
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to delete statement';
      toast.error(errorMessage);
      console.error('Delete error:', err);
      console.error('Error details:', {
        status: err?.response?.status,
        data: err?.response?.data,
        message: err?.message
      });
    }
  };

  const handleDownloadFile = async (filename: string) => {
    try {
      // Use the correct download endpoint
      const response = await fetch(`/api/bs-statement/${entity}/download/${filename}`);
      
      if (!response.ok) {
        throw new Error('Download failed');
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      toast.success('Statement downloaded successfully');
    } catch (err) {
      toast.error('Failed to download statement');
      console.error('Download error:', err);
    }
  };

  const handleViewStatement = (filename: string) => {
    setViewingStatement(filename);
  };

  return (
    <div className="mt-8 bg-white rounded-lg border-2 shadow-lg overflow-hidden" style={{ borderColor: `${PLAINFLOW_RED}33` }}>
      {/* Content */}
      <div className="p-6">
        {/* Balance Sheet Already Generated - PROMINENT DISPLAY - Show even while loading readiness */}
        {!loadingStatements && bsStatements.length > 0 && (
          <div className="mb-6 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg shadow-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <CheckCircleIcon className="w-6 h-6 text-green-700" />
                  <h2 className="text-xl font-bold text-green-900 font-satoshi">
                    Balance Sheet Already Generated!
                  </h2>
                </div>
                <p className="text-sm text-green-700 mb-2 font-satoshi">
                  Found <strong>{bsStatements.length} Balance Sheet file(s)</strong> for this entity.
                </p>
                <p className="text-sm text-green-600 font-medium font-satoshi">
                  ✅ You can download the existing statements below, view them, or re-generate.
                </p>
              </div>
            </div>
            
            {/* Quick File List */}
            <div className="mt-4 pt-4 border-t border-green-200">
              <h3 className="text-sm font-semibold text-green-900 mb-3 font-satoshi">📁 Generated Files:</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {bsStatements.slice(0, 3).map((statement, index) => (
                  <div
                    key={index}
                    className="bg-white border border-green-200 rounded p-3"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <DocumentTextIcon className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-gray-900 truncate font-satoshi">
                        {statement.filename.replace('Balance_Sheet_', '').replace('.xlsx', '')}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 font-satoshi">
                      {new Date(statement.generated_at).toLocaleDateString('en-IN', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </p>
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() => handleViewStatement(statement.filename)}
                        className="flex-1 text-xs text-blue-600 hover:text-blue-700 flex items-center justify-center gap-1 font-satoshi"
                      >
                        <EyeIcon className="w-3 h-3" />
                        View
                      </button>
                      <button
                        onClick={() => handleDownloadFile(statement.filename)}
                        className="flex-1 text-xs text-green-600 hover:text-green-700 flex items-center justify-center gap-1 font-satoshi"
                      >
                        <ArrowDownTrayIcon className="w-3 h-3" />
                        Download
                      </button>
                      <button
                        onClick={() => handleDelete(statement.filename)}
                        className="flex-1 text-xs hover:text-red-700 flex items-center justify-center gap-1 font-satoshi"
                        style={{ color: PLAINFLOW_RED }}
                      >
                        <TrashIcon className="w-3 h-3" />
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              {bsStatements.length > 3 && (
                <p className="text-xs text-green-600 mt-2 font-satoshi">
                  + {bsStatements.length - 3} more file(s) available below
                </p>
              )}
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 rounded-lg flex items-start gap-3" style={{ backgroundColor: PLAINFLOW_RED_LIGHT, borderColor: `${PLAINFLOW_RED}66`, borderWidth: '1px' }}>
            <ExclamationTriangleIcon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: PLAINFLOW_RED }} />
            <div className="flex-1">
              <p className="text-sm font-satoshi" style={{ color: PLAINFLOW_RED }}>{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="hover:opacity-75 transition-opacity"
              style={{ color: PLAINFLOW_RED }}
            >
              <XCircleIcon className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Readiness Status */}
        {loading && !readiness ? (
          <div className="mb-6 bg-gray-50 rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: PLAINFLOW_RED }}></div>
              <span className="ml-3 text-gray-600 font-satoshi">Checking statement readiness...</span>
            </div>
          </div>
        ) : readiness && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold text-gray-900 font-satoshi">
                Statement Readiness
              </h4>
              <div className="flex items-center gap-3">
                {/* Auto-refresh toggle - only show when not ready */}
                {!readiness.is_ready && (
                  <div className="flex items-center gap-2">
                    <label className="flex items-center gap-2 text-sm text-gray-600 font-satoshi cursor-pointer">
                      <input
                        type="checkbox"
                        checked={autoRefresh}
                        onChange={(e) => setAutoRefresh(e.target.checked)}
                        className="w-4 h-4 border-gray-300 rounded focus:ring-2"
                        style={{ 
                          accentColor: PLAINFLOW_RED,
                        }}
                      />
                      Auto-refresh
                    </label>
                    {autoRefresh && (
                      <span className="text-xs text-gray-500 font-satoshi">
                        ({countdown}s)
                      </span>
                    )}
                  </div>
                )}
                
                {/* Manual refresh button */}
                <button
                  onClick={checkReadiness}
                  disabled={loading}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium font-satoshi border rounded-md transition-all disabled:opacity-50"
                  style={{
                    color: PLAINFLOW_RED,
                    borderColor: `${PLAINFLOW_RED}66`,
                    backgroundColor: loading ? 'transparent' : 'white'
                  }}
                  onMouseEnter={(e) => !loading && (e.currentTarget.style.backgroundColor = PLAINFLOW_RED_LIGHT)}
                  onMouseLeave={(e) => !loading && (e.currentTarget.style.backgroundColor = 'white')}
                >
                  <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                  {loading ? 'Checking...' : 'Check Now'}
                </button>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600 font-satoshi">
                  {readiness.total_found} of {readiness.total_required} notes available
                </span>
                <span className="text-sm font-semibold text-gray-900 font-satoshi">
                  {readiness.completeness_percentage}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="h-3 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${readiness.completeness_percentage}%`,
                    backgroundColor: readiness.is_ready ? '#16a34a' : PLAINFLOW_RED
                  }}
                />
              </div>
            </div>

            {/* Status Badge */}
            <div className="flex items-center gap-2 mb-4">
              {readiness.is_ready ? (
                <>
                  <CheckCircleIcon className="w-5 h-5 text-green-600" />
                  <span className="text-green-700 font-semibold font-satoshi">
                    All notes are ready!
                  </span>
                </>
              ) : (
                <>
                  <XCircleIcon className="w-5 h-5" style={{ color: PLAINFLOW_RED }} />
                  <span className="font-semibold font-satoshi" style={{ color: PLAINFLOW_RED }}>
                    Missing {readiness.missing_notes.length} notes
                  </span>
                </>
              )}
            </div>

            {/* Missing Notes */}
            {!readiness.is_ready && readiness.missing_notes.length > 0 && (
              <div className="mb-4 p-4 rounded-lg" style={{ backgroundColor: PLAINFLOW_RED_LIGHT, borderColor: `${PLAINFLOW_RED}66`, borderWidth: '1px' }}>
                <p className="text-sm font-semibold text-gray-900 mb-2 font-satoshi">
                  Missing Notes:
                </p>
                <div className="flex flex-wrap gap-2">
                  {readiness.missing_notes.map((note) => (
                    <span
                      key={note}
                      className="px-3 py-1 bg-white rounded-full text-xs font-medium font-satoshi"
                      style={{ borderColor: `${PLAINFLOW_RED}66`, borderWidth: '1px', color: PLAINFLOW_RED }}
                    >
                      Note {note}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-gray-600 mt-3 font-satoshi">
                  Please generate the missing notes before creating the Balance Sheet.
                  {autoRefresh && (
                    <span className="block mt-1" style={{ color: PLAINFLOW_RED }}>
                      Auto-refreshing every 10 seconds to check for updates...
                    </span>
                  )}
                </p>
              </div>
            )}

            {/* Note Details Summary - Simplified cards matching P&L */}
            {readiness.is_ready && readiness.config && (
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <p className="text-xs text-blue-700 font-semibold mb-1 font-satoshi">
                    Assets Notes
                  </p>
                  <p className="text-2xl font-bold text-blue-700 font-satoshi">
                    {(readiness.config.non_current_assets?.length || 0) + (readiness.config.current_assets?.length || 0)}
                  </p>
                </div>
                <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                  <p className="text-xs text-green-700 font-semibold mb-1 font-satoshi">
                    Equity Notes
                  </p>
                  <p className="text-2xl font-bold text-green-700 font-satoshi">
                    {readiness.config.equity?.length || 0}
                  </p>
                </div>
                <div className="rounded-lg p-4 border" style={{ backgroundColor: PLAINFLOW_RED_LIGHT, borderColor: `${PLAINFLOW_RED}66` }}>
                  <p className="text-xs font-semibold mb-1 font-satoshi" style={{ color: PLAINFLOW_RED }}>
                    Liabilities Notes
                  </p>
                  <p className="text-2xl font-bold font-satoshi" style={{ color: PLAINFLOW_RED }}>
                    {(readiness.config.non_current_liabilities?.length || 0) + (readiness.config.current_liabilities?.length || 0)}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleGenerate}
            disabled={!readiness?.is_ready || generating}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all font-satoshi disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              backgroundColor: readiness?.is_ready && !generating ? PLAINFLOW_RED : '#d1d5db',
              color: readiness?.is_ready && !generating ? 'white' : '#6b7280'
            }}
            onMouseEnter={(e) => {
              if (readiness?.is_ready && !generating) {
                e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER;
              }
            }}
            onMouseLeave={(e) => {
              if (readiness?.is_ready && !generating) {
                e.currentTarget.style.backgroundColor = PLAINFLOW_RED;
              }
            }}
          >
            {generating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Generating Balance Sheet...
              </>
            ) : (
              <>
                <DocumentTextIcon className="w-5 h-5" />
                Generate Balance Sheet
              </>
            )}
          </button>
        </div>

        {/* Last Generated Info */}
        {lastGenerated && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-700 font-satoshi">
              <CheckCircleIcon className="w-4 h-4 inline mr-2" />
              Balance Sheet generated successfully at {new Date(lastGenerated).toLocaleString()}
            </p>
          </div>
        )}
      </div>

      {/* Statement Viewer Modal */}
      {viewingStatement && (
        <StatementViewer
          filename={viewingStatement}
          companyName={entity}
          statementType="bs"
          onClose={() => setViewingStatement(null)}
        />
      )}
    </div>
  );
};

export default BalanceSheetGenerator;