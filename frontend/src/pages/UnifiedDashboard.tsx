import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import { 
  ChartBarIcon, 
  DocumentTextIcon, 
  CheckCircleIcon,
  XCircleIcon,
  BuildingOfficeIcon,
  FolderOpenIcon,
  DocumentDuplicateIcon,
  TableCellsIcon
} from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { Entity } from '../config/entities';

interface EntityFileStatus {
  entity: string;
  entityName: string;
  currencySymbol?: string;
  hasTrialBalance: boolean;
  adjustmentFileCount: number;
  hasMappingFile: boolean;
  inputFiles: {
    trialBalance: boolean;
    adjustments: boolean;
    mapping: boolean;
  };
}

const UnifiedDashboard: React.FC = () => {
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);

  const { data: apiEntities, isLoading: isLoadingEntities } = useQuery(
    'entities',
    async () => {
      const response = await apiService.getEntities();
      return response.data as Entity[];
    },
    {
      staleTime: 5 * 60 * 1000,
      placeholderData: [],
    }
  );

  const entities = useMemo(() => {
    if (!Array.isArray(apiEntities)) return [];
    return apiEntities.map((e: any) => ({
      code: e.code || e.short_code,
      short_code: e.short_code || e.code,
      name: e.name,
      currency: e.currency,
    }));
  }, [apiEntities]);

  // Fetch files for all entities
  const entityCodes = entities.map(e => e.short_code || e.code).filter(Boolean);
  
  const { data: allEntityFiles, isLoading } = useQuery(
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
      enabled: entityCodes.length > 0,
    }
  );

  // Process entity file status
  const getEntityFileStatus = (entityCode: string, filesData: any): EntityFileStatus => {
    const entityMeta = entities.find(e => (e.short_code || e.code) === entityCode);
    const entityName = entityMeta?.name || entityCode;
    const currencySymbol = entityMeta?.currency?.symbol;
    
    if (!filesData) {
      return {
        entity: entityCode,
        entityName,
        hasTrialBalance: false,
        adjustmentFileCount: 0,
        hasMappingFile: false,
        inputFiles: {
          trialBalance: false,
          adjustments: false,
          mapping: false,
        },
      };
    }

    const unadjustedTB = filesData.unadjusted_trialbalance || [];
    const manualAdjustments = filesData.manual_adjustments || [];
    const configFiles = filesData.config || [];
    
    // Helper to extract filename from file object or string
    const getFilename = (f: any): string => {
      return typeof f === 'string' ? f : f.filename || '';
    };
    
    // Check for trial balance files
    const hasTrialBalance = unadjustedTB.some((f: any) => {
      const filename = getFilename(f).toLowerCase();
      return filename.includes('trial') || 
        filename.includes('tb') ||
        filename.includes('balance') ||
        filename.endsWith('.csv') ||
        filename.endsWith('.xlsx');
    });

    // Count adjustment files
    const adjustmentFileCount = manualAdjustments.filter((f: any) => {
      const filename = getFilename(f);
      return filename.endsWith('.xlsx') || filename.endsWith('.csv');
    }).length;

    // Check for mapping file in config folder (standard name: glcode_major_minor_mappings.xlsx)
    const hasMappingFile = configFiles.some((f: any) => {
      const filename = getFilename(f).toLowerCase();
      return filename.includes('glcode_major_minor_mappings') ||
        filename.includes('mapping') || 
        filename.includes('map');
    });

    return {
      entity: entityCode,
      entityName,
      hasTrialBalance,
      adjustmentFileCount,
      hasMappingFile,
      inputFiles: {
        trialBalance: hasTrialBalance,
        adjustments: adjustmentFileCount > 0,
        mapping: hasMappingFile,
      },
      currencySymbol: currencySymbol || '',
    };
  };

  const entityStatuses: EntityFileStatus[] = allEntityFiles?.map((result: any) => 
    getEntityFileStatus(result.entity, result.files)
  ) || [];

  // Overall statistics
  const totalEntities = entityStatuses.length;
  const entitiesWithTB = entityStatuses.filter(s => s.hasTrialBalance).length;
  const entitiesWithAdj = entityStatuses.filter(s => s.adjustmentFileCount > 0).length;
  const entitiesWithMapping = entityStatuses.filter(s => s.hasMappingFile).length;

  // Get selected entity details
  const selectedEntityDetails = selectedEntity 
    ? entityStatuses.find(s => s.entity === selectedEntity)
    : null;

  const part1Steps = [
    {
      id: 1,
      name: 'Upload Trial Balance',
      href: '/step1',
      icon: DocumentTextIcon,
      fileKey: 'trialBalance' as const,
    },
    {
      id: 2,
      name: 'Upload Adjustments',
      href: '/step2',
      icon: DocumentTextIcon,
      fileKey: 'adjustments' as const,
    },
    {
      id: 3,
      name: 'Apply Adjustments',
      href: '/step3',
      icon: CheckCircleIcon,
      fileKey: null,
    },
    {
      id: 4,
      name: 'Map Categories',
      href: '/step4',
      icon: TableCellsIcon,
      fileKey: 'mapping' as const,
    },
    {
      id: 5,
      name: 'Validate 6 Rules',
      href: '/step5',
      icon: CheckCircleIcon,
      fileKey: null,
    },
  ];

  const part2Steps = [
    {
      id: 6,
      name: 'Generate Notes',
      href: '/step6',
      icon: DocumentTextIcon,
    },
    {
      id: 7,
      name: 'Generate P&L',
      href: '/step7',
      icon: ChartBarIcon,
    },
    {
      id: 8,
      name: 'Generate Balance Sheet',
      href: '/step8',
      icon: ChartBarIcon,
    },
    {
      id: 9,
      name: 'Generate Cash Flow',
      href: '/step9',
      icon: ChartBarIcon,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-lg shadow-lg">
        <div className="px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <ChartBarIcon className="h-12 w-12 text-white" />
              <div className="ml-4">
                <h1 className="text-3xl font-bold text-white">Dashboard</h1>
                <p className="mt-2 text-primary-100">
                  Financial Close Process Overview
                </p>
              </div>
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
              <p className="text-sm font-medium text-gray-600">With Trial Balance</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{entitiesWithTB}</p>
            </div>
            <DocumentTextIcon className="h-12 w-12 text-green-500 opacity-50" />
          </div>
        </div>

        <div className="card bg-white border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">With Adjustments</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{entitiesWithAdj}</p>
            </div>
            <DocumentDuplicateIcon className="h-12 w-12 text-blue-500 opacity-50" />
          </div>
        </div>

        <div className="card bg-white border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">With Mapping</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{entitiesWithMapping}</p>
            </div>
            <TableCellsIcon className="h-12 w-12 text-purple-500 opacity-50" />
          </div>
        </div>
      </div>

      {/* Entities Overview */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <FolderOpenIcon className="h-6 w-6 mr-2 text-primary-600" />
          Entities Being Worked Upon
        </h2>
        
        {isLoading || isLoadingEntities ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <span className="ml-3 text-gray-600">Loading entities...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entity
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trial Balance
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Adjustments
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Mapping
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {entityStatuses.map((entity) => (
                  <tr 
                    key={entity.entity}
                    className={`hover:bg-gray-50 transition-colors ${
                      selectedEntity === entity.entity ? 'bg-primary-50' : ''
                    }`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <BuildingOfficeIcon className="h-5 w-5 text-gray-400 mr-2" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {entity.entityName} {entity.currencySymbol && (
                              <span className="text-xs text-gray-600 font-normal">
                                ({entity.currencySymbol})
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-gray-500">{entity.entity}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {entity.hasTrialBalance ? (
                        <CheckCircleIcon className="h-6 w-6 text-green-500 mx-auto" />
                      ) : (
                        <XCircleIcon className="h-6 w-6 text-red-400 mx-auto" />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {entity.adjustmentFileCount > 0 ? (
                        <div className="flex items-center justify-center">
                          <CheckCircleIcon className="h-6 w-6 text-green-500" />
                          <span className="ml-2 text-sm text-gray-700">
                            ({entity.adjustmentFileCount})
                          </span>
                        </div>
                      ) : (
                        <XCircleIcon className="h-6 w-6 text-red-400 mx-auto" />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {entity.hasMappingFile ? (
                        <CheckCircleIcon className="h-6 w-6 text-green-500 mx-auto" />
                      ) : (
                        <XCircleIcon className="h-6 w-6 text-red-400 mx-auto" />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <button
                        onClick={() => setSelectedEntity(
                          selectedEntity === entity.entity ? null : entity.entity
                        )}
                        className="text-primary-600 hover:text-primary-900 text-sm font-medium"
                      >
                        {selectedEntity === entity.entity ? 'Hide Details' : 'View Details'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Selected Entity Details */}
      {selectedEntity && selectedEntityDetails && (
        <div className="card bg-gradient-to-br from-primary-50 to-white border-2 border-primary-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Process Details: {selectedEntityDetails.entityName}
          </h2>

          {/* PART 1: Trial Balance Preparation */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-primary-900 mb-3 flex items-center">
              <span className="bg-primary-100 text-primary-800 px-2 py-1 rounded text-sm mr-2">
                PART 1
              </span>
              Trial Balance Preparation
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {part1Steps.map((step) => {
                const hasInputFile = step.fileKey 
                  ? selectedEntityDetails.inputFiles[step.fileKey]
                  : null;
                
                return (
                  <Link
                    key={step.id}
                    to={step.href}
                    className="block bg-white rounded-lg border-2 border-gray-200 hover:border-primary-500 transition-all duration-200 p-4"
                  >
                    <div className="flex items-start">
                      <div className={`flex-shrink-0 ${
                        hasInputFile === true 
                          ? 'text-green-600' 
                          : hasInputFile === false 
                          ? 'text-red-400' 
                          : 'text-gray-400'
                      }`}>
                        {hasInputFile === true ? (
                          <CheckCircleIcon className="h-8 w-8" />
                        ) : hasInputFile === false ? (
                          <XCircleIcon className="h-8 w-8" />
                        ) : (
                          <step.icon className="h-8 w-8" />
                        )}
                      </div>
                      <div className="ml-3">
                        <h4 className="text-sm font-medium text-gray-900">
                          {step.name}
                        </h4>
                        <p className="mt-1 text-xs text-gray-500">
                          {hasInputFile === true && 'File Available'}
                          {hasInputFile === false && 'No File'}
                          {hasInputFile === null && 'Process Step'}
                        </p>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* PART 2: Financial Statement Generation */}
          <div>
            <h3 className="text-lg font-semibold text-primary-900 mb-3 flex items-center">
              <span className="bg-primary-100 text-primary-800 px-2 py-1 rounded text-sm mr-2">
                PART 2
              </span>
              Financial Statement Generation
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {part2Steps.map((step) => (
                <Link
                  key={step.id}
                  to={step.href}
                  className="block bg-white rounded-lg border-2 border-gray-200 hover:border-primary-500 transition-all duration-200 p-4"
                >
                  <div className="flex items-start">
                    <div className="flex-shrink-0 text-gray-400">
                      <step.icon className="h-8 w-8" />
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-gray-900">
                        {step.name}
                      </h4>
                      <p className="mt-1 text-xs text-gray-500">
                        Generation Step
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UnifiedDashboard;
