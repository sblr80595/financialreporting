// src/components/statements/StatementHeader.tsx

import React from 'react';
import { 
  ArrowDownTrayIcon, 
  PrinterIcon, 
  ShareIcon 
} from '@heroicons/react/24/outline';
import { StatementType, Framework, DesignTokens } from '../../types/statement';

interface StatementHeaderProps {
  title: string;
  subtitle: string;
  statementType: StatementType;
  framework: Framework;
  onFrameworkChange: (framework: Framework) => void;
  entityScope: 'Standalone' | 'Consolidated';
  onEntityScopeChange: (scope: 'Standalone' | 'Consolidated') => void;
  periodLabel: string;
  onPeriodClick?: () => void;
  currency: string;
  rounding: string;
  onExport?: () => void;
  onPrint?: () => void;
  onShare?: () => void;
  showCashFlowMethod?: boolean;
  cashFlowMethod?: 'Indirect' | 'Direct';
  onCashFlowMethodChange?: (method: 'Indirect' | 'Direct') => void;
}

const StatementHeader: React.FC<StatementHeaderProps> = ({
  title,
  subtitle,
  statementType,
  framework,
  onFrameworkChange,
  entityScope,
  onEntityScopeChange,
  periodLabel,
  onPeriodClick,
  currency,
  rounding,
  onExport,
  onPrint,
  onShare,
  showCashFlowMethod,
  cashFlowMethod,
  onCashFlowMethodChange,
}) => {
  return (
    <div 
      className="bg-white rounded-lg border p-6 shadow-sm mb-6 font-satoshi"
      style={{ borderColor: DesignTokens.colors.border.subtle }}
    >
      <div className="flex items-center justify-between">
        {/* Left: Title and Tags */}
        <div>
          <h1 
            className="font-semibold mb-1"
            style={DesignTokens.text.h1}
          >
            {title}
          </h1>
          <p 
            className="mb-3"
            style={{ ...DesignTokens.text.body, color: DesignTokens.colors.text.muted }}
          >
            {subtitle}
          </p>
          <div className="flex items-center gap-2">
            <span 
              className="px-2 py-1 rounded text-xs font-medium"
              style={{
                backgroundColor: DesignTokens.colors.primary[100],
                color: DesignTokens.colors.primary[500],
              }}
            >
              {framework === 'IndAS' ? 'Ind AS • Schedule III' : 'IFRS • IAS 1'}
            </span>
          </div>
        </div>

        {/* Right: Controls and Actions */}
        <div className="flex items-center gap-4">
          {/* Framework Selector */}
          <div className="flex flex-col">
            <label 
              className="text-xs mb-1"
              style={{ color: DesignTokens.colors.text.muted }}
            >
              Reporting Framework
            </label>
            <select
              value={framework}
              onChange={(e) => onFrameworkChange(e.target.value as Framework)}
              className="px-3 py-1.5 border rounded text-sm font-medium focus:outline-none focus:ring-2"
              style={{
                borderColor: DesignTokens.colors.border.subtle,
                color: DesignTokens.colors.text.default,
              }}
            >
              <option value="IndAS">Ind AS (Schedule III)</option>
              <option value="IFRS">IFRS (IAS 1)</option>
            </select>
          </div>

          {/* Cash Flow Method (conditional) */}
          {showCashFlowMethod && (
            <div className="flex flex-col">
              <label 
                className="text-xs mb-1"
                style={{ color: DesignTokens.colors.text.muted }}
              >
                Method
              </label>
              <select
                value={cashFlowMethod}
                onChange={(e) => onCashFlowMethodChange?.(e.target.value as 'Indirect' | 'Direct')}
                className="px-3 py-1.5 border rounded text-sm font-medium focus:outline-none focus:ring-2"
                style={{
                  borderColor: DesignTokens.colors.border.subtle,
                  color: DesignTokens.colors.text.default,
                }}
              >
                <option value="Indirect">Indirect</option>
                <option value="Direct">Direct</option>
              </select>
            </div>
          )}

          {/* Entity Scope */}
          <div className="flex flex-col">
            <label 
              className="text-xs mb-1"
              style={{ color: DesignTokens.colors.text.muted }}
            >
              Entity Scope
            </label>
            <select
              value={entityScope}
              onChange={(e) => onEntityScopeChange(e.target.value as 'Standalone' | 'Consolidated')}
              className="px-3 py-1.5 border rounded text-sm font-medium focus:outline-none focus:ring-2"
              style={{
                borderColor: DesignTokens.colors.border.subtle,
                color: DesignTokens.colors.text.default,
              }}
            >
              <option value="Standalone">Standalone</option>
              <option value="Consolidated">Consolidated</option>
            </select>
          </div>

          {/* Period Selector */}
          <div className="flex flex-col">
            <label 
              className="text-xs mb-1"
              style={{ color: DesignTokens.colors.text.muted }}
            >
              Period
            </label>
            <button
              onClick={onPeriodClick}
              className="px-3 py-1.5 border rounded text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2"
              style={{
                borderColor: DesignTokens.colors.border.subtle,
                color: DesignTokens.colors.text.default,
              }}
            >
              {periodLabel}
            </button>
          </div>

          {/* Currency & Rounding Display */}
          <div className="flex flex-col">
            <label 
              className="text-xs mb-1"
              style={{ color: DesignTokens.colors.text.muted }}
            >
              Currency & Rounding
            </label>
            <div 
              className="px-3 py-1.5 rounded text-sm font-medium"
              style={{
                backgroundColor: DesignTokens.colors.surface.subtle,
                color: DesignTokens.colors.text.default,
              }}
            >
              {currency}, {rounding}
            </div>
          </div>

          {/* Divider */}
          <div 
            className="w-px h-10"
            style={{ backgroundColor: DesignTokens.colors.border.subtle }}
          />

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {onExport && (
              <button
                onClick={onExport}
                className="p-2 border rounded hover:bg-gray-50 transition-colors"
                style={{
                  borderColor: DesignTokens.colors.border.subtle,
                }}
                title="Export"
              >
                <ArrowDownTrayIcon className="w-5 h-5" />
              </button>
            )}
            {onPrint && (
              <button
                onClick={onPrint}
                className="p-2 border rounded hover:bg-gray-50 transition-colors"
                style={{
                  borderColor: DesignTokens.colors.border.subtle,
                }}
                title="Print"
              >
                <PrinterIcon className="w-5 h-5" />
              </button>
            )}
            {onShare && (
              <button
                onClick={onShare}
                className="p-2 border rounded hover:bg-gray-50 transition-colors"
                style={{
                  borderColor: DesignTokens.colors.border.subtle,
                }}
                title="Share"
              >
                <ShareIcon className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatementHeader;
