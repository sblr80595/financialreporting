// src/components/statements/ReadinessPanel.tsx

import React from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { StatementReadiness, DesignTokens } from '../../types/statement';

interface ReadinessPanelProps {
  readiness: StatementReadiness;
  onRequirementClick?: (requirementId: string) => void;
}

const ReadinessPanel: React.FC<ReadinessPanelProps> = ({ 
  readiness, 
  onRequirementClick 
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircleIcon className="w-5 h-5" style={{ color: DesignTokens.colors.status.success }} />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-5 h-5" style={{ color: DesignTokens.colors.status.warn }} />;
      case 'error':
        return <XCircleIcon className="w-5 h-5" style={{ color: DesignTokens.colors.status.error }} />;
      case 'pending':
        return <ClockIcon className="w-5 h-5" style={{ color: DesignTokens.colors.text.muted }} />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'done':
        return '✅ Done';
      case 'warning':
        return '⚠️ Warning';
      case 'error':
        return '❌ Error';
      case 'pending':
        return '⏳ Pending';
      default:
        return status;
    }
  };

  return (
    <div 
      className="bg-white rounded-lg border p-6 shadow-sm mb-6 font-satoshi"
      style={{ 
        borderColor: DesignTokens.colors.border.subtle,
        boxShadow: DesignTokens.elevation.card,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 style={DesignTokens.text.h2}>
            Statement Readiness
          </h2>
        </div>
        <div 
          className="px-3 py-1 rounded"
          style={{
            backgroundColor: DesignTokens.colors.surface.subtle,
          }}
        >
          <span 
            className="font-semibold"
            style={{ 
              ...DesignTokens.text.caption,
              color: readiness.isReady 
                ? DesignTokens.colors.status.success 
                : DesignTokens.colors.status.warn 
            }}
          >
            {readiness.completionPercentage}% COMPLETE
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span 
            className="text-sm"
            style={{ color: DesignTokens.colors.text.muted }}
          >
            {readiness.isReady 
              ? 'All requirements met' 
              : `${readiness.requirements.filter(r => r.status === 'done').length} of ${readiness.requirements.length} requirements complete`
            }
          </span>
          <span 
            className="text-sm font-semibold"
            style={{ color: DesignTokens.colors.text.default }}
          >
            {readiness.completionPercentage}%
          </span>
        </div>
        <div 
          className="w-full rounded-full h-3"
          style={{ backgroundColor: DesignTokens.colors.surface.subtle }}
        >
          <div
            className="h-3 rounded-full transition-all duration-500"
            style={{ 
              width: `${readiness.completionPercentage}%`,
              backgroundColor: readiness.isReady 
                ? DesignTokens.colors.status.success 
                : DesignTokens.colors.status.warn
            }}
          />
        </div>
      </div>

      {/* Requirements Table */}
      <div className="space-y-2">
        {/* Table Header */}
        <div 
          className="grid grid-cols-12 gap-4 py-2 px-3 rounded"
          style={{ 
            backgroundColor: DesignTokens.colors.surface.subtle,
            ...DesignTokens.text.tableHeader,
          }}
        >
          <div className="col-span-5">Requirement</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-5">Details</div>
        </div>

        {/* Table Rows */}
        {readiness.requirements.map((req, index) => (
          <div
            key={req.id}
            className={`grid grid-cols-12 gap-4 py-3 px-3 rounded transition-colors ${
              req.clickable ? 'cursor-pointer hover:bg-gray-50' : ''
            }`}
            style={{
              backgroundColor: index % 2 === 0 
                ? DesignTokens.colors.surface.default 
                : DesignTokens.colors.surface.subtle,
              borderLeft: `3px solid ${
                req.status === 'done' 
                  ? DesignTokens.colors.status.success 
                  : req.status === 'warning'
                  ? DesignTokens.colors.status.warn
                  : req.status === 'error'
                  ? DesignTokens.colors.status.error
                  : 'transparent'
              }`,
            }}
            onClick={() => req.clickable && onRequirementClick?.(req.id)}
          >
            <div 
              className="col-span-5 flex items-center"
              style={{ ...DesignTokens.text.body, color: DesignTokens.colors.text.default }}
            >
              {req.name}
            </div>
            <div className="col-span-2 flex items-center gap-2">
              {getStatusIcon(req.status)}
              <span 
                className="text-xs font-medium"
                style={{
                  color: req.status === 'done' 
                    ? DesignTokens.colors.status.success 
                    : req.status === 'warning'
                    ? DesignTokens.colors.status.warn
                    : req.status === 'error'
                    ? DesignTokens.colors.status.error
                    : DesignTokens.colors.text.muted
                }}
              >
                {getStatusText(req.status)}
              </span>
            </div>
            <div 
              className="col-span-5 flex items-center text-sm"
              style={{ color: DesignTokens.colors.text.muted }}
            >
              {req.details || '—'}
            </div>
          </div>
        ))}
      </div>

      {/* Last Updated */}
      <div 
        className="mt-4 pt-4 border-t text-xs"
        style={{ 
          borderColor: DesignTokens.colors.border.subtle,
          color: DesignTokens.colors.text.muted,
        }}
      >
        Last checked: {new Date(readiness.lastUpdated).toLocaleString('en-IN', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })}
      </div>
    </div>
  );
};

export default ReadinessPanel;
