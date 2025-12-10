// src/types/index.ts

export interface Company {
  name: string;
  csv_file: string;
  notes_count: number;
  notes: NoteInfo[];
}

export interface NoteInfo {
  number: string;
  title: string;
}

export interface GenerationResponse {
  success: boolean;
  message: string;
  note_number?: string;
  output_file?: string;
  content?: string;
}

export interface BatchResponse {
  message: string;
  batch_id: string;
  status_url: string;
}

export interface BatchStatus {
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_notes: number;
  completed_notes: number;
  current_note: string | null;
  results: GenerationResponse[];
}

export type GenerationStatusType = 'idle' | 'loading' | 'success' | 'error';

export interface GenerationStatusMap {
  [key: string]: GenerationStatusType;
}

export interface NoteCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  notes: NoteInfo[];
}

export interface CompanyCategories {
  company_name: string;
  categories: NoteCategory[];
}

// ============================================================================
// P&L Statement Types
// ============================================================================
export interface PLReadinessResponse {
  company_name: string;
  is_ready: boolean;
  found_notes: string[];
  missing_notes: string[];
  note_details: {
    [key: string]: {
      description: string;
      amount: number;
      file_path: string;
      generated_at: string;
    };
  };
  total_required: number;
  total_found: number;
  completeness_percentage: number;
  config: {
    income_notes: string[];
    expense_notes: string[];
    tax_notes: string[];
  };
}

export interface PLGenerationRequest {
  company_name: string;
  period_ended: string;
  note_numbers: string[];
}

export interface PLLineItem {
  particulars: string;
  note: string | null;
  amount: number;
  is_subtotal: boolean;
  is_total: boolean;
  indent_level: number;
}

export interface PLSection {
  section_name: string;
  line_items: PLLineItem[];
}

export interface PLStatement {
  company_name: string;
  period_ended: string;
  sections: PLSection[];
  metadata: {
    generated_at: string;
    notes_used: string[];
    config_used: {
      income_notes: string[];
      expense_notes: string[];
      tax_notes: string[];
    };
  };
}

export interface PLGenerationResponse {
  success: boolean;
  message: string;
  statement: PLStatement;
  output_file: string;
  html_preview: string | null;
}

export interface PLStatementFile {
  filename: string;
  file_path: string;
  size_bytes: number;
  generated_at: string;
  download_url: string;
}

export interface PLStatementsListResponse {
  company_name: string;
  statements: PLStatementFile[];
  count: number;
  latest: PLStatementFile | null;
}

// ============================================================================
// Generated Notes Types
// ============================================================================
export interface GeneratedNoteFile {
  filename: string;
  file_path: string;
  note_number: string | null;
  title: string | null;
  size_bytes: number;
  generated_at: number;
  download_url: string;
}

export interface GeneratedNotesListResponse {
  company_name: string;
  category_id: string | null;
  notes: GeneratedNoteFile[];
  count: number;
}

export interface NoteContentResponse {
  filename: string;
  content: string;
}