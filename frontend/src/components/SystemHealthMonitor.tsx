import React, { useEffect, useState } from 'react';
import { Activity, AlertCircle, CheckCircle, Clock, Database, Server, Zap } from 'lucide-react';
import apiService from '../services/apiService';
import { LoadingSpinner } from './LoadingStates';
import notificationService from '../services/notificationService';

interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
  services: Record<string, string>;
  uptime_seconds?: number;
}

interface ServiceStatusProps {
  name: string;
  status: string;
  icon: React.ReactNode;
}

const ServiceStatus: React.FC<ServiceStatusProps> = ({ name, status, icon }) => {
  const isHealthy = status === 'healthy' || status === 'ok';
  const statusColor = isHealthy ? 'text-green-600' : 'text-red-600';
  const bgColor = isHealthy ? 'bg-green-50' : 'bg-red-50';
  const borderColor = isHealthy ? 'border-green-200' : 'border-red-200';

  return (
    <div className={`${bgColor} ${borderColor} border rounded-lg p-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={statusColor}>{icon}</div>
          <div>
            <h3 className="text-sm font-medium text-gray-900">{name}</h3>
            <p className={`text-xs ${statusColor}`}>{status}</p>
          </div>
        </div>
        {isHealthy ? (
          <CheckCircle className="w-5 h-5 text-green-600" />
        ) : (
          <AlertCircle className="w-5 h-5 text-red-600" />
        )}
      </div>
    </div>
  );
};

const SystemHealthMonitor: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.get<HealthStatus>('/api/health');
      setHealth(response);
      setLastChecked(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to fetch health status');
      notificationService.error('Failed to fetch system health');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds?: number): string => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (loading && !health) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <AlertCircle className="w-6 h-6 text-red-600" />
          <div>
            <h3 className="text-sm font-medium text-red-900">System Health Check Failed</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchHealth}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const isSystemHealthy = health?.status === 'healthy';

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Activity className={`w-8 h-8 ${isSystemHealthy ? 'text-green-600' : 'text-red-600'}`} />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">System Health</h2>
              <p className="text-sm text-gray-500">
                Last checked: {lastChecked.toLocaleTimeString()}
              </p>
            </div>
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Checking...' : 'Refresh'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Zap className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Status</span>
            </div>
            <p className={`text-lg font-bold ${isSystemHealthy ? 'text-green-600' : 'text-red-600'}`}>
              {health?.status?.toUpperCase()}
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Clock className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Uptime</span>
            </div>
            <p className="text-lg font-bold text-gray-900">
              {formatUptime(health?.uptime_seconds)}
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Server className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Version</span>
            </div>
            <p className="text-lg font-bold text-gray-900">{health?.version}</p>
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Service Status</h3>
          
          {health?.services && Object.entries(health.services).map(([serviceName, status]) => {
            let icon = <Server className="w-5 h-5" />;
            let displayName = serviceName;

            if (serviceName === 'api') {
              icon = <Server className="w-5 h-5" />;
              displayName = 'API Server';
            } else if (serviceName === 'llm') {
              icon = <Zap className="w-5 h-5" />;
              displayName = 'AI/LLM Service';
            } else if (serviceName === 'file_system') {
              icon = <Database className="w-5 h-5" />;
              displayName = 'File System';
            } else if (serviceName === 'companies_discovered') {
              displayName = `Companies (${status})`;
              status = 'healthy';
            }

            return (
              <ServiceStatus
                key={serviceName}
                name={displayName}
                status={status}
                icon={icon}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SystemHealthMonitor;
