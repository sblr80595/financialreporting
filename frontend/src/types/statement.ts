// Statement Template Types

export type StatementType = 'PnL' | 'BalanceSheet' | 'CashFlow';
export type Framework = 'IndAS' | 'IFRS';
export type CashFlowMethod = 'Indirect' | 'Direct';
export type RowType = 'section' | 'group' | 'lineItem' | 'subtotal' | 'spacer' | 'total';
export type ColumnType = 'text' | 'amount' | 'noteRef' | 'calculated';
export type Alignment = 'left' | 'right' | 'center';
export type Sign = 'normal' | 'invert';
export type MappingSource = 'GL' | 'Tag' | 'Manual';
export type CalcOp = 'sum' | 'diff' | 'custom';

export interface StatementTemplate {
  id: string;
  statementType: StatementType;
  framework: Framework;
  method?: CashFlowMethod;
  version: number;
  meta: StatementMeta;
  columns: ColumnDef[];
  rows: StatementRow[];
}

export interface StatementMeta {
  title: string;
  subtitlePattern: string;
  currencyLabelDefault: string;
}

export interface ColumnDef {
  id: string;
  label: string;
  type: ColumnType;
  alignment: Alignment;
  width?: number | 'flex';
  format?: 'amount' | 'percent' | 'eps' | 'custom';
}

export interface StatementRow {
  id: string;
  label: string;
  type: RowType;
  section?: string;
  parentId?: string;
  order: number;
  style?: RowStyle;
  noteNumber?: string | null;
  calculation?: CalcExpression;
  sign?: Sign;
  mappings?: MappingRule[];
}

export interface RowStyle {
  bold?: boolean;
  italic?: boolean;
  uppercase?: boolean;
  backgroundToken?: string;
  indentLevel?: number;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export type CalcExpression =
  | { op: 'sum'; children: string[] }
  | { op: 'diff'; minuend: string; subtrahend: string }
  | { op: 'custom'; formula: string };

export interface MappingRule {
  source: MappingSource;
  glRanges?: GLRange[];
  tags?: string[];
  sign?: Sign;
}

export interface GLRange {
  from: string;
  to: string;
}

// Statement Viewer Props
export interface StatementViewerProps {
  companyName: string;
  statementType: StatementType;
  framework?: Framework;
  method?: CashFlowMethod;
}

// Statement Data (runtime values)
export interface StatementData {
  template: StatementTemplate;
  values: StatementValueMap;
  periodEnd: string;
  comparisonEnd?: string;
  currency: string;
  rounding: string;
  entityScope: 'Standalone' | 'Consolidated';
}

export interface StatementValueMap {
  [rowId: string]: {
    current?: number | null;
    previous?: number | null;
    note?: string;
  };
}

// Readiness Status
export interface StatementReadiness {
  isReady: boolean;
  completionPercentage: number;
  requirements: ReadinessRequirement[];
  lastUpdated: string;
}

export interface ReadinessRequirement {
  id: string;
  name: string;
  status: 'done' | 'warning' | 'error' | 'pending';
  details?: string;
  clickable?: boolean;
}

// Generated Statement File Info
export interface GeneratedStatement {
  filename: string;
  statementType: StatementType;
  framework: Framework;
  generatedAt: string;
  periodEnd: string;
  fileSize?: number;
  url?: string;
}

// Design Tokens (matching Figma spec)
export const DesignTokens = {
  colors: {
    primary: {
      500: '#0F62FE',
      100: '#E5EEFF',
    },
    surface: {
      default: '#FFFFFF',
      subtle: '#F7F8FA',
      sectionBlue: '#F2F7FF',
      sectionPurple: '#F7F2FF',
      subtotal: '#F5F5F5',
      total: '#E8E8E8',
      totalStrong: '#D4D4D4',
    },
    border: {
      subtle: '#E0E3EB',
    },
    text: {
      default: '#1F2430',
      muted: '#6B7280',
    },
    status: {
      success: '#12B981',
      warn: '#F59E0B',
      error: '#EF4444',
    },
  },
  text: {
    h1: {
      fontSize: '24px',
      fontWeight: 600,
      lineHeight: '32px',
    },
    h2: {
      fontSize: '18px',
      fontWeight: 600,
    },
    body: {
      fontSize: '14px',
      fontWeight: 400,
    },
    bodyBold: {
      fontSize: '14px',
      fontWeight: 600,
    },
    caption: {
      fontSize: '12px',
      fontWeight: 400,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.04em',
    },
    tableHeader: {
      fontSize: '13px',
      fontWeight: 600,
      textTransform: 'uppercase' as const,
    },
  },
  elevation: {
    card: '0px 1px 2px 0px rgba(15, 23, 42, 0.08)',
  },
} as const;

// Helper function to get background color from token
export function getBackgroundColor(token?: string): string {
  if (!token) return DesignTokens.colors.surface.default;
  
  const parts = token.split('.');
  if (parts.length !== 2) return DesignTokens.colors.surface.default;
  
  const [category, variant] = parts;
  if (category === 'surface') {
    return DesignTokens.colors.surface[variant as keyof typeof DesignTokens.colors.surface] || DesignTokens.colors.surface.default;
  }
  
  return DesignTokens.colors.surface.default;
}

// Helper to calculate indent padding
export function getIndentPadding(level: number = 0): string {
  return `${16 + level * 12}px`;
}
