import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  ChartBarIcon, 
  DocumentTextIcon, 
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { useQuery } from 'react-query';
import { apiService } from '../services/api';
import { ENTITIES } from '../config/entities';

const Dashboard: React.FC = () => {
  // Use the first entity's short_code as default
  const [selectedEntity, setSelectedEntity] = useState<string>(ENTITIES[0]?.short_code || 'cpm');
  
  const { data: entities, isLoading: entitiesLoading } = useQuery(
    'entities',
    () => apiService.getEntities(),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const { data: health, isLoading: healthLoading } = useQuery(
    'health',
    () => apiService.getHealth(),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchInterval: false, // Disable automatic polling
    }
  );

  const workflowSteps = [
    {
      id: 1,
      name: 'Upload Trial Balance',
      description: 'Extract from SAP or upload manually',
      href: '/step1',
      icon: DocumentTextIcon,
      status: 'pending',
      part: 'PART 1: Trial Balance Preparation'
    },
    {
      id: 2,
      name: 'Upload Manual Adjustments',
      description: 'Upload 6 adjustment types',
      href: '/step2',
      icon: DocumentTextIcon,
      status: 'pending',
      part: 'PART 1: Trial Balance Preparation'
    },
    {
      id: 3,
      name: 'Apply Adjustments',
      description: 'Execute adjustments & view results',
      href: '/step3',
      icon: CheckCircleIcon,
      status: 'pending',
      part: 'PART 1: Trial Balance Preparation'
    },
    {
      id: 4,
      name: 'Map Categories',
      description: 'Apply Major/Minor category mapping',
      href: '/step4',
      icon: CheckCircleIcon,
      status: 'pending',
      part: 'PART 1: Trial Balance Preparation'
    },
    {
      id: 5,
      name: 'Validate 6 Rules',
      description: 'Validate Final Adjusted TB',
      href: '/step5',
      icon: CheckCircleIcon,
      status: 'pending',
      part: 'PART 1: Trial Balance Preparation'
    },
    {
      id: 6,
      name: 'Generate Notes',
      description: 'Individual or batch note generation',
      href: '/step6',
      icon: DocumentTextIcon,
      status: 'pending',
      part: 'PART 2: Financial Statement Generation'
    },
    {
      id: 7,
      name: 'Generate P&L',
      description: 'Profit & Loss Statement',
      href: '/step7',
      icon: ChartBarIcon,
      status: 'pending',
      part: 'PART 2: Financial Statement Generation'
    },
    // {
    //   id: 8,
    //   name: 'Generate BS Notes',
    //   description: 'Balance Sheet related notes',
    //   href: '/step8',
    //   icon: DocumentTextIcon,
    //   status: 'pending',
    //   part: 'PART 2: Financial Statement Generation'
    // },
    {
      id: 8,
      name: 'Generate Balance Sheet',
      description: 'Balance Sheet Statement',
      href: '/step8',
      icon: ChartBarIcon,
      status: 'pending',
      part: 'PART 2: Financial Statement Generation'
    },
    {
      id: 9,
      name: 'Generate Cash Flow',
      description: 'Cash Flow Statement',
      href: '/step9',
      icon: ChartBarIcon,
      status: 'pending',
      part: 'PART 2: Financial Statement Generation'
    }
  ];

  const groupedSteps = workflowSteps.reduce((acc, step) => {
    const part = step.part;
    if (!acc[part]) {
      acc[part] = [];
    }
    acc[part].push(step);
    return acc;
  }, {} as Record<string, typeof workflowSteps>);

  return (
    <div className="space-y-6">
      {/* Entity Selection */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🏢 Choose Entity</h2>
        {entitiesLoading ? (
          <div className="animate-pulse">Loading entities...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {entities?.data?.map((entity: any) => (
              <button
                key={entity.code}
                onClick={() => setSelectedEntity(entity.short_code || entity.code)}
                className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                  selectedEntity === (entity.short_code || entity.code)
                    ? 'border-primary-500 bg-primary-50 text-primary-900'
                    : 'border-gray-200 hover:border-gray-300 text-gray-700'
                }`}
              >
                <div className="text-center">
                  <div className="text-sm font-medium">{entity.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{entity.code}</div>
                </div>
              </button>
            ))}
          </div>
        )}
        
        {selectedEntity && (
          <div className="mt-4 p-3 bg-primary-100 rounded-lg">
            <span className="text-sm font-medium text-primary-900">
              Selected: {entities?.data?.find((e: any) => (e.short_code || e.code) === selectedEntity)?.name} ({selectedEntity})
            </span>
          </div>
        )}
      </div>

      {/* System Status */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
        {healthLoading ? (
          <div className="animate-pulse">Checking system status...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="flex items-center p-3 bg-green-50 rounded-lg">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <div className="ml-3">
                <div className="text-sm font-medium text-green-900">API Status</div>
                <div className="text-xs text-green-600">
                  {health?.data?.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
                </div>
              </div>
            </div>
            <div className="flex items-center p-3 bg-blue-50 rounded-lg">
              <ClockIcon className="h-6 w-6 text-blue-600" />
              <div className="ml-3">
                <div className="text-sm font-medium text-blue-900">Last Updated</div>
                <div className="text-xs text-blue-600">
                  {health?.data?.timestamp ? new Date(health.data.timestamp).toLocaleTimeString() : 'Unknown'}
                </div>
              </div>
            </div>
            <div className="flex items-center p-3 bg-purple-50 rounded-lg">
              <ChartBarIcon className="h-6 w-6 text-purple-600" />
              <div className="ml-3">
                <div className="text-sm font-medium text-purple-900">AI Orchestrator</div>
                <div className="text-xs text-purple-600">
                  {(health?.data as any)?.services?.ai_orchestrator === 'available' ? 'Available' : 'Unavailable'}
                </div>
              </div>
            </div>
            <div className="flex items-center p-3 bg-orange-50 rounded-lg">
              <DocumentTextIcon className="h-6 w-6 text-orange-600" />
              <div className="ml-3">
                <div className="text-sm font-medium text-orange-900">File Service</div>
                <div className="text-xs text-orange-600">
                  {(health?.data as any)?.services?.file_service === 'available' ? 'Available' : 'Unavailable'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Workflow Steps */}
      <div className="space-y-6">
        {Object.entries(groupedSteps).map(([part, steps]) => (
          <div key={part} className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{part}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {steps.map((step) => (
                <Link
                  key={step.id}
                  to={step.href}
                  className="group block p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:shadow-md transition-all duration-200"
                >
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <step.icon className="h-8 w-8 text-primary-600 group-hover:text-primary-700" />
                    </div>
                    <div className="ml-3 flex-1">
                      <div className="flex items-center">
                        <span className="step-indicator pending mr-2">
                          {step.id}
                        </span>
                        <h3 className="text-sm font-medium text-gray-900 group-hover:text-primary-700">
                          {step.name}
                        </h3>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">
                        {step.description}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/step1"
            className="btn-primary w-full text-center"
          >
            Start New Processing
          </Link>
          <Link
            to="/feedback"
            className="btn-secondary w-full text-center"
          >
            Submit Feedback
          </Link>
          <button
            onClick={() => window.location.reload()}
            className="btn-secondary w-full"
          >
            Refresh Status
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
