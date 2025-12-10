// src/components/statements/StatementTable.tsx

import React, { useState } from 'react';
import { ChevronRightIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { 
  StatementRow, 
  ColumnDef, 
  StatementValueMap, 
  DesignTokens,
  getBackgroundColor,
  getIndentPadding
} from '../../types/statement';

interface StatementTableProps {
  columns: ColumnDef[];
  rows: StatementRow[];
  values: StatementValueMap;
  onNoteClick?: (noteNumber: string) => void;
  onRowClick?: (rowId: string) => void;
  currency?: string;
  rounding?: string;
}

const StatementTable: React.FC<StatementTableProps> = ({
  columns,
  rows,
  values,
  onNoteClick,
  onRowClick,
  currency = 'INR',
  rounding = 'Lakhs',
}) => {
  const [collapsedRows, setCollapsedRows] = useState<Set<string>>(new Set());

  const toggleCollapse = (rowId: string) => {
    setCollapsedRows(prev => {
      const next = new Set(prev);
      if (next.has(rowId)) {
        next.delete(rowId);
      } else {
        next.add(rowId);
      }
      return next;
    });
  };

  const isRowVisible = (row: StatementRow): boolean => {
    if (!row.parentId) return true;
    
    // Check if any parent is collapsed
    let currentRow: StatementRow | undefined = row;
    while (currentRow?.parentId) {
      const parentId: string = currentRow.parentId;
      const parent: StatementRow | undefined = rows.find(r => r.id === parentId);
      if (!parent) break;
      
      if (collapsedRows.has(parent.id)) {
        return false;
      }
      
      currentRow = parent;
    }
    
    return true;
  };

  const formatAmount = (amount: number | null | undefined): string => {
    if (amount === null || amount === undefined) return '—';
    
    // Format with Indian number system (lakhs/crores)
    const absAmount = Math.abs(amount);
    const formatted = absAmount.toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    
    return amount < 0 ? `(${formatted})` : formatted;
  };

  const renderCellContent = (column: ColumnDef, row: StatementRow) => {
    const rowValue = values[row.id] || {};

    switch (column.id) {
      case 'particulars':
        return (
          <div 
            className="flex items-center gap-2"
            style={{ paddingLeft: getIndentPadding(row.style?.indentLevel) }}
          >
            {row.style?.collapsible && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleCollapse(row.id);
                }}
                className="flex-shrink-0 hover:bg-gray-100 rounded p-0.5 transition-colors"
              >
                {collapsedRows.has(row.id) ? (
                  <ChevronRightIcon className="w-4 h-4" />
                ) : (
                  <ChevronDownIcon className="w-4 h-4" />
                )}
              </button>
            )}
            <span 
              className={`${row.style?.bold ? 'font-semibold' : ''} ${row.style?.italic ? 'italic' : ''} ${row.style?.uppercase ? 'uppercase' : ''}`}
              style={{ fontSize: DesignTokens.text.body.fontSize }}
            >
              {row.label}
            </span>
          </div>
        );

      case 'note':
        if (row.noteNumber || rowValue.note) {
          const noteNum = rowValue.note || row.noteNumber;
          return (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onNoteClick?.(noteNum!);
              }}
              className="text-blue-600 hover:text-blue-800 hover:underline text-sm font-medium"
            >
              {noteNum}
            </button>
          );
        }
        return <span className="text-gray-400">—</span>;

      case 'current':
        return (
          <span 
            className={`${row.style?.bold ? 'font-semibold' : ''} tabular-nums`}
            style={{ fontSize: DesignTokens.text.body.fontSize }}
          >
            {formatAmount(rowValue.current)}
          </span>
        );

      case 'previous':
        return (
          <span 
            className={`${row.style?.bold ? 'font-semibold' : ''} tabular-nums`}
            style={{ fontSize: DesignTokens.text.body.fontSize }}
          >
            {formatAmount(rowValue.previous)}
          </span>
        );

      default:
        return <span>—</span>;
    }
  };

  const getRowClassName = (row: StatementRow) => {
    const classes = ['transition-colors'];
    
    if (row.type === 'section' || row.type === 'total') {
      classes.push('border-t-2 border-b');
    }
    
    if (onRowClick) {
      classes.push('cursor-pointer hover:bg-gray-50');
    }
    
    return classes.join(' ');
  };

  return (
    <div 
      className="bg-white rounded-lg border shadow-sm overflow-hidden font-satoshi"
      style={{ 
        borderColor: DesignTokens.colors.border.subtle,
        boxShadow: DesignTokens.elevation.card,
      }}
    >
      {/* Table Header - Sticky */}
      <div 
        className="sticky top-0 z-10 grid border-b-2"
        style={{ 
          gridTemplateColumns: columns.map(c => 
            c.width === 'flex' ? '1fr' : `${c.width}px`
          ).join(' '),
          backgroundColor: DesignTokens.colors.surface.subtle,
          borderColor: DesignTokens.colors.border.subtle,
        }}
      >
        {columns.map((column) => (
          <div
            key={column.id}
            className="px-4 py-3"
            style={{
              textAlign: column.alignment,
              ...DesignTokens.text.tableHeader,
              color: DesignTokens.colors.text.default,
            }}
          >
            {column.label}
          </div>
        ))}
      </div>

      {/* Table Body */}
      <div className="divide-y" style={{ borderColor: DesignTokens.colors.border.subtle }}>
        {rows
          .filter(isRowVisible)
          .sort((a, b) => a.order - b.order)
          .map((row, index) => (
            <div
              key={row.id}
              className={getRowClassName(row)}
              style={{
                display: 'grid',
                gridTemplateColumns: columns.map(c => 
                  c.width === 'flex' ? '1fr' : `${c.width}px`
                ).join(' '),
                backgroundColor: getBackgroundColor(row.style?.backgroundToken),
                minHeight: row.type === 'section' ? '52px' : '40px',
              }}
              onClick={() => onRowClick?.(row.id)}
            >
              {columns.map((column) => (
                <div
                  key={`${row.id}-${column.id}`}
                  className="px-4 py-3 flex items-center"
                  style={{
                    justifyContent: column.alignment === 'right' ? 'flex-end' 
                      : column.alignment === 'center' ? 'center' 
                      : 'flex-start',
                  }}
                >
                  {renderCellContent(column, row)}
                </div>
              ))}
            </div>
          ))}
      </div>

      {/* Footer with Balance Check (for Balance Sheet) */}
      {rows.some(r => r.id === 'TOTAL_ASSETS' || r.id === 'TOTAL_EQUITY_LIAB') && (
        <div 
          className="border-t-2 px-4 py-3 text-sm"
          style={{ 
            borderColor: DesignTokens.colors.border.subtle,
            backgroundColor: DesignTokens.colors.surface.subtle,
          }}
        >
          {(() => {
            const totalAssets = values['TOTAL_ASSETS']?.current || 0;
            const totalEquityLiab = values['TOTAL_EQUITY_LIAB']?.current || 0;
            const balanced = Math.abs(totalAssets - totalEquityLiab) < 0.01;
            
            return (
              <div className="flex items-center justify-center gap-2">
                {balanced ? (
                  <>
                    <span style={{ color: DesignTokens.colors.status.success }}>✔</span>
                    <span style={{ color: DesignTokens.colors.status.success, fontWeight: 600 }}>
                      Balanced: Assets equal Equity and Liabilities
                    </span>
                  </>
                ) : (
                  <>
                    <span style={{ color: DesignTokens.colors.status.error }}>✘</span>
                    <span style={{ color: DesignTokens.colors.status.error, fontWeight: 600 }}>
                      Out of balance by {currency} {formatAmount(Math.abs(totalAssets - totalEquityLiab))} {rounding}
                    </span>
                  </>
                )}
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default StatementTable;
