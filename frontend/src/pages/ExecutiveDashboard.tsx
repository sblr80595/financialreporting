import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { 
  BuildingOfficeIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ClockIcon,
  ChartBarIcon,
  FolderOpenIcon,
  ArrowPathIcon,
  ExclamationCircleIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { ENTITIES } from '../config/entities';

interface EntityStatus {
  entity: string;
  entityName: string;
  sapConnectivity?: {
    available: boolean;
    entityName?: string;
    status?: string;
  };
  sourceFiles: {
    trialBalance: boolean;
    adjustments: number;
  };
  adjustmentsApplied: {
    rollForward: boolean;
    rollBack: boolean;
    gtIndia: boolean;
    interco: boolean;
    reclassification: boolean;
    encCorrect: boolean;
  };
  finalOutputs: {
    finalTrialBalance: boolean;
    validationReport: boolean;
    profitLoss: boolean;
    balanceSheet: boolean;
    cashFlow: boolean;
    notes: number;
  };
  lastProcessed: string | null;
  status: 'not_started' | 'in_progress' | 'completed' | 'error';
}

const ExecutiveDashboard: React.FC = () => {
  const [selectedEntity, setSelectedEntity] = useState<string>('all');

  // Fetch files for all entities
  const entityCodes = ENTITIES.map(e => e.short_code);
  
  const entityFilesQueries = useQuery(
    ['all-entity-files', entityCodes],
    async () => {
      const results = await Promise.all(
        entityCodes.map(async (code) => {
          try {
            const files = await apiService.listEntityFiles(code);
            return { entity: code, files: files.data };
          } catch (error) {
            return { entity: code, files: null };
          }
        })
      );
      return results;
    },
    {
      staleTime: 300000, // 5 minutes
    }
  );

  // Fetch SAP connectivity for all entities
  const sapConnectivityQueries = useQuery(
    ['all-sap-connectivity', entityCodes],
    async () => {
      const results = await Promise.all(
        entityCodes.map(async (code) => {
          try {
            const connectivity = await apiService.checkSAPConnectivity(code);
            return { entity: code, sap: connectivity.data };
          } catch (error) {
            return { entity: code, sap: null };
          }
        })
      );
      return results;
    },
    {
      staleTime: 600000, // 10 minutes (SAP connectivity doesn't change often)
    }
  );

  // Process entity status from files
  const getEntityStatus = (entityCode: string, filesData: any): EntityStatus => {
    if (!filesData) {
      return {
        entity: entityCode,
        entityName: ENTITIES.find(e => e.short_code === entityCode)?.name || entityCode,
        sourceFiles: { trialBalance: false, adjustments: 0 },
        adjustmentsApplied: {
          rollForward: false,
          rollBack: false,
          gtIndia: false,
          interco: false,
          reclassification: false,
          encCorrect: false,
        },
        finalOutputs: {
          finalTrialBalance: false,
          validationReport: false,
          profitLoss: false,
          balanceSheet: false,
          cashFlow: false,
          notes: 0,
        },
        lastProcessed: null,
        status: 'not_started',
      };
    }

    // API returns: unadjusted_trialbalance, manual_adjustments, adjusted_trialbalance, generated_notes, financial_statements
    const unadjustedTB = filesData.unadjusted_trialbalance || [];
    const manualAdjustments = filesData.manual_adjustments || [];
    const adjustedTB = filesData.adjusted_trialbalance || [];
    const generatedNotes = filesData.generated_notes || [];
    const financialStatements = filesData.financial_statements || [];

    // Count adjustment files in manual_adjustments folder
    const adjustmentPatterns = [
      'rf_audit',
      'rb_audit',
      'audit_adjustment', // gt_india
      'interco',
      'reclass',
      'enc_correct'
    ];

    const adjustmentCount = adjustmentPatterns.filter(pattern => 
      manualAdjustments.some((f: string) => f.toLowerCase().includes(pattern))
    ).length;

    // Check for reconciliation files (indicate adjustments were applied)
    const adjustmentsApplied = {
      rollForward: adjustedTB.some((f: string) => f.includes('rf_audit_adjustments_reconciliation')),
      rollBack: adjustedTB.some((f: string) => f.includes('rb_audit_adjustments_reconciliation')),
      gtIndia: adjustedTB.some((f: string) => f.includes('gt_india_audit_adjustments_reconciliation')),
      interco: adjustedTB.some((f: string) => f.includes('interco_adjustments_reconciliation')),
      reclassification: adjustedTB.some((f: string) => f.includes('reclass_entries_reconciliation')),
      encCorrect: adjustedTB.some((f: string) => f.includes('enc_correct_period_reconciliation')),
    };

    // Check for final outputs
    const finalOutputs = {
      finalTrialBalance: adjustedTB.some((f: string) => f.includes('final_trial_balance')),
      validationReport: adjustedTB.some((f: string) => f.includes('TB_Validation_7Rules_Report') || f.includes('Validation')),
      profitLoss: financialStatements.some((f: string) => 
        f.toLowerCase().includes('profit') || 
        f.toLowerCase().includes('p&l') || 
        f.toLowerCase().includes('p_l') ||
        f.toLowerCase().includes('income')
      ),
      balanceSheet: financialStatements.some((f: string) => 
        f.toLowerCase().includes('balance_sheet') || 
        f.toLowerCase().includes('balance sheet')
      ),
      cashFlow: financialStatements.some((f: string) => 
        f.toLowerCase().includes('cash_flow') || 
        f.toLowerCase().includes('cash flow')
      ),
      notes: generatedNotes.filter((f: string) => 
        f.toLowerCase().includes('note') && 
        (f.endsWith('.md') || f.endsWith('.xlsx') || f.endsWith('.docx'))
      ).length,
    };

    // Determine status
    let status: EntityStatus['status'] = 'not_started';
    if (unadjustedTB.length > 0 || manualAdjustments.length > 0) {
      status = 'in_progress';
    }
    if (finalOutputs.finalTrialBalance && finalOutputs.validationReport) {
      status = 'completed';
    }

    return {
      entity: entityCode,
      entityName: ENTITIES.find(e => e.short_code === entityCode)?.name || entityCode,
      sourceFiles: {
        trialBalance: unadjustedTB.some((f: string) => 
          f.toLowerCase().includes('trial') || 
          f.toLowerCase().includes('tb') ||
          f.toLowerCase().includes('balance')
        ),
        adjustments: adjustmentCount,
      },
      adjustmentsApplied,
      finalOutputs,
      lastProcessed: null, // Can be enhanced with file modification dates
      status,
    };
  };

  const entityStatuses: EntityStatus[] = entityFilesQueries.data?.map((result: any) => {
    const status = getEntityStatus(result.entity, result.files);
    
    // Add SAP connectivity info
    const sapInfo = sapConnectivityQueries.data?.find((s: any) => s.entity === result.entity);
    if (sapInfo?.sap) {
      status.sapConnectivity = {
        available: sapInfo.sap.available || false,
        entityName: sapInfo.sap.entity_name,
        status: sapInfo.sap.status
      };
    }
    
    return status;
  }) || [];

  const filteredStatuses = selectedEntity === 'all' 
    ? entityStatuses 
    : entityStatuses.filter(s => s.entity === selectedEntity);

  // Overall statistics
  const totalEntities = entityStatuses.length;
  const completedEntities = entityStatuses.filter(s => s.status === 'completed').length;
  const inProgressEntities = entityStatuses.filter(s => s.status === 'in_progress').length;
  const notStartedEntities = entityStatuses.filter(s => s.status === 'not_started').length;

  const getStatusColor = (status: EntityStatus['status']) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'not_started': return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
    }
  };

  const getStatusIcon = (status: EntityStatus['status']) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'in_progress': return <ArrowPathIcon className="h-5 w-5 text-yellow-600" />;
      case 'not_started': return <ClockIcon className="h-5 w-5 text-gray-600" />;
      case 'error': return <ExclamationCircleIcon className="h-5 w-5 text-red-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Executive Header */}
            {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-lg shadow-soft">
        <div className="px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <ChartBarIcon className="h-12 w-12 text-white" />
              <div className="ml-4">
                <h1 className="text-3xl font-bold text-white">
                  Executive Dashboard
                </h1>
                <p className="mt-2 text-primary-100">
                  Consolidated view of financial close process across all entities
                </p>
              </div>
            </div>
            <div className="text-right text-white">
              <div className="text-sm text-primary-200">Current Period</div>
              <div className="text-xl font-semibold">March 2025</div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card bg-white border-l-4 border-indigo-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Entities</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{totalEntities}</p>
            </div>
            <BuildingOfficeIcon className="h-12 w-12 text-indigo-500 opacity-50" />
          </div>
        </div>

        <div className="card bg-white border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{completedEntities}</p>
              <p className="text-xs text-gray-500 mt-1">
                {totalEntities > 0 ? Math.round((completedEntities / totalEntities) * 100) : 0}% complete
              </p>
            </div>
            <CheckCircleIcon className="h-12 w-12 text-green-500 opacity-50" />
          </div>
        </div>

        <div className="card bg-white border-l-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">In Progress</p>
              <p className="text-3xl font-bold text-yellow-600 mt-2">{inProgressEntities}</p>
              <p className="text-xs text-gray-500 mt-1">Active processing</p>
            </div>
            <ArrowPathIcon className="h-12 w-12 text-yellow-500 opacity-50" />
          </div>
        </div>

        <div className="card bg-white border-l-4 border-gray-400">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Not Started</p>
              <p className="text-3xl font-bold text-gray-600 mt-2">{notStartedEntities}</p>
              <p className="text-xs text-gray-500 mt-1">Pending</p>
            </div>
            <ClockIcon className="h-12 w-12 text-gray-400 opacity-50" />
          </div>
        </div>
      </div>

      {/* Entity Filter */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Filter by Entity</h2>
          <select
            value={selectedEntity}
            onChange={(e) => setSelectedEntity(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="all">All Entities</option>
            {ENTITIES.map(entity => (
              <option key={entity.short_code} value={entity.short_code}>
                {entity.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Entity Status Cards */}
      <div className="space-y-4">
        {filteredStatuses.map((entityStatus) => (
          <div key={entityStatus.entity} className="card bg-white shadow-md hover:shadow-lg transition-shadow">
            {/* Entity Header */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
              <div className="flex items-center">
                <BuildingOfficeIcon className="h-8 w-8 text-indigo-600 mr-3" />
                <div>
                  <h3 className="text-xl font-bold text-gray-900">{entityStatus.entityName}</h3>
                  <p className="text-sm text-gray-500">{entityStatus.entity.toUpperCase()}</p>
                </div>
              </div>
              <div className={`px-4 py-2 rounded-full border flex items-center space-x-2 ${getStatusColor(entityStatus.status)}`}>
                {getStatusIcon(entityStatus.status)}
                <span className="text-sm font-semibold capitalize">{entityStatus.status.replace('_', ' ')}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Source Files */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <FolderOpenIcon className="h-5 w-5 mr-2 text-blue-600" />
                  Source Files
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">Trial Balance</span>
                    {entityStatus.sourceFiles.trialBalance ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-600" />
                    ) : (
                      <ClockIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">Adjustments</span>
                    <span className="text-sm font-semibold text-indigo-600">
                      {entityStatus.sourceFiles.adjustments} files
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">SAP/ERP</span>
                    {entityStatus.sapConnectivity?.available ? (
                      <div className="flex items-center text-xs text-green-600">
                        <CheckCircleIcon className="h-4 w-4 mr-1" />
                        Connected
                      </div>
                    ) : (
                      <div className="flex items-center text-xs text-gray-400">
                        <ExclamationCircleIcon className="h-4 w-4 mr-1" />
                        Not Available
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Adjustments Applied */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <ArrowPathIcon className="h-5 w-5 mr-2 text-purple-600" />
                  Adjustments Applied
                </h4>
                <div className="space-y-2">
                  {Object.entries(entityStatus.adjustmentsApplied).map(([key, applied]) => (
                    <div key={key} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-xs text-gray-700">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </span>
                      {applied ? (
                        <CheckCircleIcon className="h-4 w-4 text-green-600" />
                      ) : (
                        <ClockIcon className="h-4 w-4 text-gray-400" />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Final Outputs */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <DocumentTextIcon className="h-5 w-5 mr-2 text-green-600" />
                  Final Outputs
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">Final TB</span>
                    {entityStatus.finalOutputs.finalTrialBalance ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-600" />
                    ) : (
                      <ClockIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">Validation Report</span>
                    {entityStatus.finalOutputs.validationReport ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-600" />
                    ) : (
                      <ClockIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">P&L Statement</span>
                    {entityStatus.finalOutputs.profitLoss ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-600" />
                    ) : (
                      <ClockIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">Balance Sheet</span>
                    {entityStatus.finalOutputs.balanceSheet ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-600" />
                    ) : (
                      <ClockIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">Cash Flow</span>
                    {entityStatus.finalOutputs.cashFlow ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-600" />
                    ) : (
                      <ClockIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">Notes Generated</span>
                    <span className="text-sm font-semibold text-indigo-600">
                      {entityStatus.finalOutputs.notes}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {entityStatuses.length === 0 && (
        <div className="card text-center py-12">
          <CalendarIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No entity data available yet</p>
          <p className="text-sm text-gray-500 mt-2">Start processing entities to see their status here</p>
        </div>
      )}
    </div>
  );
};

export default ExecutiveDashboard;
