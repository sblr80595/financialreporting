// src/components/statements/FinancialStatementViewer.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowDownTrayIcon, 
  EyeIcon,
  TrashIcon,
  DocumentTextIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import StatementHeader from './StatementHeader';
import ReadinessPanel from './ReadinessPanel';
import StatementTable from './StatementTable';
import { 
  StatementType, 
  Framework, 
  StatementTemplate,
  StatementValueMap,
  StatementReadiness,
  GeneratedStatement,
  DesignTokens
} from '../../types/statement';
import { usePeriod } from '../../contexts/PeriodContext';

interface FinancialStatementViewerProps {
  companyName: string;
  statementType: StatementType;
}

const FinancialStatementViewer: React.FC<FinancialStatementViewerProps> = ({
  companyName,
  statementType,
}) => {
  const { currentPeriodColumn } = usePeriod();
  const navigate = useNavigate();
  
  // State
  const [framework, setFramework] = useState<Framework>('IndAS');
  const [cashFlowMethod, setCashFlowMethod] = useState<'Indirect' | 'Direct'>('Indirect');
  const [entityScope, setEntityScope] = useState<'Standalone' | 'Consolidated'>('Standalone');
  const [periodEnd] = useState(currentPeriodColumn || 'MAR-2025');
  const [template, setTemplate] = useState<StatementTemplate | null>(null);
  const [values, setValues] = useState<StatementValueMap>({});
  const [readiness, setReadiness] = useState<StatementReadiness | null>(null);
  const [generatedStatements, setGeneratedStatements] = useState<GeneratedStatement[]>([]);
  const [loading, setLoading] = useState(false);

  // Load template based on framework and statement type
  useEffect(() => {
    loadTemplate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [framework, statementType, cashFlowMethod]);

  // Load statement data
  useEffect(() => {
    if (template) {
      loadStatementData();
      loadGeneratedStatements();
      checkReadiness();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyName, statementType, periodEnd, template]);

  const loadTemplate = async () => {
    try {
      let templatePath = '';
      
      if (statementType === 'PnL') {
        templatePath = framework === 'IndAS' 
          ? '/statement_templates/pl_indas.json'
          : '/statement_templates/pl_ifrs.json';
      } else if (statementType === 'BalanceSheet') {
        templatePath = framework === 'IndAS'
          ? '/statement_templates/bs_indas.json'
          : '/statement_templates/bs_ifrs.json';
      } else if (statementType === 'CashFlow') {
        templatePath = `/statement_templates/cf_indas_${cashFlowMethod.toLowerCase()}.json`;
      }

      // Fetch template from public folder
      const response = await fetch(templatePath);
      if (!response.ok) {
        throw new Error(`Failed to fetch template: ${response.statusText}`);
      }
      const templateData: StatementTemplate = await response.json();
      setTemplate(templateData);
      console.log('[StatementViewer] Template loaded:', templateData.id);
    } catch (error) {
      console.error('Error loading template:', error);
      toast.error('Failed to load statement template');
    }
  };
  const loadStatementData = async () => {
    if (!template) {
      console.log('[StatementViewer] Template not loaded yet, skipping data load');
      return;
    }
    
    try {
      setLoading(true);
      console.log('[StatementViewer] Loading actual statement data from backend...');
      
      // Normalize company name to match backend expectations
      // Convert to lowercase and replace spaces with underscores
      const normalizedCompanyName = companyName.toLowerCase().replace(/\s+/g, '_');
      console.log('[StatementViewer] Company:', companyName, '-> Normalized:', normalizedCompanyName);
      console.log('[StatementViewer] Statement:', statementType);
      
      // Import apiService
      const { default: api } = await import('../../services/api');
      
      // Map statement type to backend format
      let backendStatementType = '';
      if (statementType === 'PnL') {
        backendStatementType = 'pl';
      } else if (statementType === 'BalanceSheet') {
        backendStatementType = 'bs';
      } else if (statementType === 'CashFlow') {
        backendStatementType = 'cf';
      }
      
      console.log('[StatementViewer] Calling API with:', backendStatementType, normalizedCompanyName);
      
      // Call backend API to get statement data
      const response = await api.legacy.getStatementData(backendStatementType, normalizedCompanyName);
      
      console.log('[StatementViewer] API response:', response);
      
      if (response.success && response.data) {
        // Backend returns data in format: { row_id: { current: number, previous: number } }
        // Convert to StatementValueMap format
        const loadedValues: StatementValueMap = {};
        
        template.rows.forEach(row => {
          const backendValue = response.data[row.id];
          if (backendValue) {
            loadedValues[row.id] = {
              current: backendValue.current,
              previous: backendValue.previous,
              note: row.noteNumber || undefined,
            };
          } else {
            // No data for this row - show empty
            loadedValues[row.id] = {
              current: null,
              previous: null,
              note: row.noteNumber || undefined,
            };
          }
        });
        
        setValues(loadedValues);
        console.log('[StatementViewer] Loaded actual data for', Object.keys(response.data).length, 'rows');
        toast.success('Statement data loaded successfully');
      } else {
        throw new Error(response.message || 'No data available');
      }
    } catch (error: any) {
      console.error('Error loading statement data:', error);
      
      // If 404, show user-friendly message
      if (error?.response?.status === 404) {
        toast.error(`No generated ${statementType} statement found for ${companyName}. Please generate the statement first.`);
      } else {
        toast.error('Failed to load statement data');
      }
      
      // Fall back to empty values
      const emptyValues: StatementValueMap = {};
      template.rows.forEach(row => {
        emptyValues[row.id] = {
          current: null,
          previous: null,
          note: row.noteNumber || undefined,
        };
      });
      setValues(emptyValues);
    } finally {
      setLoading(false);
    }
  };

  const loadGeneratedStatements = async () => {
    try {
      // Call backend API to get list of generated statements
      // Placeholder for now
      const mockStatements: GeneratedStatement[] = [
        {
          filename: `${statementType}_${companyName}_${periodEnd}.xlsx`,
          statementType,
          framework,
          generatedAt: new Date().toISOString(),
          periodEnd,
          fileSize: 245000,
        }
      ];
      
      setGeneratedStatements(mockStatements);
    } catch (error) {
      console.error('Error loading generated statements:', error);
    }
  };

  const checkReadiness = async () => {
    try {
      // Call backend API to check readiness
      // Placeholder for now
      const mockReadiness: StatementReadiness = {
        isReady: true,
        completionPercentage: 100,
        lastUpdated: new Date().toISOString(),
        requirements: [
          {
            id: 'trial_balance',
            name: 'Trial balance imported',
            status: 'done',
            details: `31 ${periodEnd}, 2,340 GL accounts`,
          },
          {
            id: 'mapping',
            name: `Mapping to ${framework} ${statementType} headings`,
            status: 'done',
            details: '100% mapped',
          },
          {
            id: 'notes',
            name: 'Notes prepared',
            status: 'done',
            details: 'All required notes available',
          },
          {
            id: 'validation',
            name: 'Validations (sign & totals)',
            status: 'done',
            details: 'No differences detected',
          },
        ],
      };
      
      setReadiness(mockReadiness);
    } catch (error) {
      console.error('Error checking readiness:', error);
    }
  };

  const handleExport = () => {
    toast.success('Export functionality coming soon');
  };

  const handlePrint = () => {
    window.print();
  };

  const handleShare = () => {
    toast.success('Share functionality coming soon');
  };

  const handleNoteClick = (noteNumber: string) => {
    toast.success(`Navigating to Note ${noteNumber}`);
    // Navigate to note detail page
  };

  const handleRequirementClick = (requirementId: string) => {
    toast.success(`Navigating to ${requirementId}`);
    // Navigate to requirement page
  };

  const handleGenerateStatement = () => {
    toast.success('Statement generation initiated');
    // Call backend to generate statement
  };

  if (!template) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading statement template...</p>
        </div>
      </div>
    );
  }

  const subtitle = template.meta.subtitlePattern.replace('{periodEnd}', periodEnd);

  return (
    <div className="max-w-[1400px] mx-auto p-6 font-satoshi">
      {/* Back Button */}
      <button
        onClick={() => navigate('/view-statements')}
        className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeftIcon className="w-5 h-5" />
        <span className="font-medium">Back to Statement Selection</span>
      </button>

      {/* Header */}
      <StatementHeader
        title={template.meta.title}
        subtitle={subtitle}
        statementType={statementType}
        framework={framework}
        onFrameworkChange={setFramework}
        entityScope={entityScope}
        onEntityScopeChange={setEntityScope}
        periodLabel={periodEnd}
        onPeriodClick={() => toast('Period selector coming soon')}
        currency="INR"
        rounding="in Lakhs"
        onExport={handleExport}
        onPrint={handlePrint}
        onShare={handleShare}
        showCashFlowMethod={statementType === 'CashFlow'}
        cashFlowMethod={cashFlowMethod}
        onCashFlowMethodChange={setCashFlowMethod}
      />

      {/* Generated Statements Card */}
      {generatedStatements.length > 0 && (
        <div 
          className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 rounded-lg p-6 mb-6"
          style={{ borderColor: DesignTokens.colors.status.success }}
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <DocumentTextIcon className="w-6 h-6" style={{ color: DesignTokens.colors.status.success }} />
                <h3 className="text-lg font-semibold" style={{ color: '#065F46' }}>
                  Recent {template.meta.title} Statements
                </h3>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {generatedStatements.slice(0, 3).map((statement, index) => (
              <div
                key={index}
                className="bg-white border rounded p-4"
                style={{ borderColor: '#A7F3D0' }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <DocumentTextIcon className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-gray-900 truncate">
                    {statement.filename}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mb-3">
                  {new Date(statement.generatedAt).toLocaleDateString('en-IN', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => toast('View statement')}
                    className="flex-1 text-xs text-blue-600 hover:text-blue-700 flex items-center justify-center gap-1"
                  >
                    <EyeIcon className="w-3 h-3" />
                    View
                  </button>
                  <button
                    onClick={() => toast.success('Downloading...')}
                    className="flex-1 text-xs text-green-600 hover:text-green-700 flex items-center justify-center gap-1"
                  >
                    <ArrowDownTrayIcon className="w-3 h-3" />
                    Download
                  </button>
                  <button
                    onClick={() => toast.success('Deleted')}
                    className="flex-1 text-xs text-red-600 hover:text-red-700 flex items-center justify-center gap-1"
                  >
                    <TrashIcon className="w-3 h-3" />
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Readiness Panel */}
      {readiness && (
        <ReadinessPanel
          readiness={readiness}
          onRequirementClick={handleRequirementClick}
        />
      )}

      {/* Statement Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading statement data...</p>
          </div>
        </div>
      ) : (
        <StatementTable
          columns={template.columns}
          rows={template.rows}
          values={values}
          onNoteClick={handleNoteClick}
          currency="INR"
          rounding="Lakhs"
        />
      )}

      {/* Generate Button (if not generated yet) */}
      {readiness?.isReady && generatedStatements.length === 0 && (
        <div className="mt-6">
          <button
            onClick={handleGenerateStatement}
            className="w-full py-4 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold flex items-center justify-center gap-2"
          >
            <DocumentTextIcon className="w-5 h-5" />
            Generate {template.meta.title}
          </button>
        </div>
      )}
    </div>
  );
};

export default FinancialStatementViewer;
