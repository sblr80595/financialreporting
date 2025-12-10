// src/pages/ViewStatementsPage.tsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  DocumentTextIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { useEntity } from '../contexts/EntityContext';
import { StatementType, DesignTokens } from '../types/statement';

const ViewStatementsPage: React.FC = () => {
  const { selectedEntity } = useEntity();
  const navigate = useNavigate();

  const statements = [
    {
      type: 'PnL' as StatementType,
      name: 'Profit & Loss Statement',
      description: 'Statement of Profit and Loss (Ind AS / IFRS compliant)',
      icon: ChartBarIcon,
      color: 'blue',
      details: [
        'Revenue from operations',
        'Operating expenses breakdown',
        'Tax expense calculation',
        'Earnings per share (EPS)',
        'Other comprehensive income (OCI)',
      ],
    },
    {
      type: 'BalanceSheet' as StatementType,
      name: 'Balance Sheet',
      description: 'Statement of Financial Position (Ind AS Schedule III / IFRS IAS 1)',
      icon: DocumentTextIcon,
      color: 'purple',
      details: [
        'Non-current and current assets',
        'Equity share capital',
        'Reserves and surplus',
        'Current and non-current liabilities',
        'Balance verification (Assets = Equity + Liabilities)',
      ],
    },
    {
      type: 'CashFlow' as StatementType,
      name: 'Cash Flow Statement',
      description: 'Statement of Cash Flows (Indirect / Direct method)',
      icon: CurrencyDollarIcon,
      color: 'green',
      details: [
        'Cash flows from operating activities',
        'Cash flows from investing activities',
        'Cash flows from financing activities',
        'Net change in cash position',
        'Reconciliation with balance sheet',
      ],
    },
  ];

  const getColorClasses = (color: string) => {
    const colors = {
      blue: {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        hover: 'hover:border-blue-400 hover:bg-blue-100',
        text: 'text-blue-700',
        icon: 'text-blue-600',
      },
      purple: {
        bg: 'bg-purple-50',
        border: 'border-purple-200',
        hover: 'hover:border-purple-400 hover:bg-purple-100',
        text: 'text-purple-700',
        icon: 'text-purple-600',
      },
      green: {
        bg: 'bg-green-50',
        border: 'border-green-200',
        hover: 'hover:border-green-400 hover:bg-green-100',
        text: 'text-green-700',
        icon: 'text-green-600',
      },
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  const handleViewStatement = (type: StatementType) => {
    navigate(`/view-statements/${type.toLowerCase()}`);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 font-satoshi">
      {/* Header */}
      <div className="mb-8">
        <h1 
          className="font-semibold mb-2"
          style={DesignTokens.text.h1}
        >
          View Financial Statements
        </h1>
        <p 
          className="text-base"
          style={{ color: DesignTokens.colors.text.muted }}
        >
          Select a financial statement to view, analyze, and export for <strong>{selectedEntity}</strong>
        </p>
      </div>

      {/* Statement Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {statements.map((statement) => {
          const colors = getColorClasses(statement.color);
          const Icon = statement.icon;

          return (
            <div
              key={statement.type}
              className={`${colors.bg} ${colors.border} ${colors.hover} border-2 rounded-lg p-6 cursor-pointer transition-all shadow-sm flex flex-col`}
              onClick={() => handleViewStatement(statement.type)}
            >
              {/* Icon and Title */}
              <div className="flex items-start gap-4 mb-4">
                <div className={`${colors.bg} p-3 rounded-lg`}>
                  <Icon className={`w-8 h-8 ${colors.icon}`} />
                </div>
                <div className="flex-1">
                  <h3 className={`text-lg font-semibold ${colors.text} mb-1`}>
                    {statement.name}
                  </h3>
                </div>
              </div>

              {/* Description */}
              <p 
                className="text-sm mb-4"
                style={{ color: DesignTokens.colors.text.muted }}
              >
                {statement.description}
              </p>

              {/* Key Features */}
              <div className="space-y-2 mb-4 flex-1">
                <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: DesignTokens.colors.text.muted }}>
                  Key Components:
                </p>
                {statement.details.slice(0, 3).map((detail, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <span className={`text-xs mt-0.5 ${colors.text}`}>•</span>
                    <span className="text-xs" style={{ color: DesignTokens.colors.text.default }}>
                      {detail}
                    </span>
                  </div>
                ))}
                {statement.details.length > 3 && (
                  <p className="text-xs" style={{ color: DesignTokens.colors.text.muted }}>
                    + {statement.details.length - 3} more features
                  </p>
                )}
              </div>

              {/* View Button */}
              <button
                className={`w-full py-2 px-4 ${colors.bg} border ${colors.border} rounded-lg font-semibold text-sm ${colors.text} flex items-center justify-center gap-2 hover:shadow-md transition-all mt-auto`}
              >
                View Statement
                <ArrowRightIcon className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>

      {/* Info Panel */}
      <div 
        className="mt-8 bg-white border rounded-lg p-6 shadow-sm"
        style={{ borderColor: DesignTokens.colors.border.subtle }}
      >
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold mb-2" style={{ color: DesignTokens.colors.text.default }}>
              About Statement Viewer
            </h3>
            <p className="text-sm mb-3" style={{ color: DesignTokens.colors.text.muted }}>
              The statement viewer provides an interactive, drill-down view of your financial statements. You can:
            </p>
            <ul className="text-sm space-y-1" style={{ color: DesignTokens.colors.text.muted }}>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">✓</span>
                <span>Switch between Ind AS (Schedule III) and IFRS (IAS 1) frameworks</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">✓</span>
                <span>View comparative periods (current year vs previous year)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">✓</span>
                <span>Drill down into note details by clicking on note references</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">✓</span>
                <span>Export statements to Excel, PDF, or print format</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">✓</span>
                <span>Collapse and expand sections for easier navigation</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ViewStatementsPage;
