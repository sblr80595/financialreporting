// FILE: src/services/api.ts
// Consolidated API service for all financial statement operations

import axios from 'axios';
import {
  Company,
  GenerationResponse,
  BatchStatus,
  NoteCategory,
  PLReadinessResponse,
  PLGenerationRequest,
  PLGenerationResponse,
  PLStatementsListResponse,
  GeneratedNotesListResponse,
  NoteContentResponse
} from '../types';

// Use empty string to make requests through React dev server proxy
// In production, this would be set via REACT_APP_API_URL environment variable
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

// ============================================
// COMMON INTERFACES
// ============================================

export interface NoteDetail {
  description: string;
  amount: number | null;
  file_path: string;
  generated_at: string;
}

export interface StatementReadinessResponse {
  company_name: string;
  is_ready: boolean;
  found_notes: string[];
  missing_notes: string[];
  note_details: Record<string, NoteDetail>;
  total_required: number;
  total_found: number;
  completeness_percentage: number;
  config?: {
    non_current_assets?: string[];
    current_assets?: string[];
    equity?: string[];
    non_current_liabilities?: string[];
    current_liabilities?: string[];
  };
}

export interface StatementGenerationRequest {
  company_name: string;
  as_at_date?: string;
  for_period?: string;
  cpm_category?: string; // Make it optional for dynamic use
}

export interface StatementGenerationResponse {
  success: boolean;
  message: string;
  statement?: any;
  output_file?: string;
}

export interface StatementFile {
  filename: string;
  file_path: string;
  size_bytes: number;
  generated_at: string;
  download_url: string;
}

// Legacy types
export interface ProcessingStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  entity: string;
  start_time: string;
  end_time?: string;
  result?: {
    success: boolean;
    message: string;
    output_files?: string[];
    execution_time?: number;
    adjustments?: any[];
  };
}

export interface EntityInfo {
  code: string;
  name: string;
  short_code?: string;
  description?: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
}

export interface GetPeriodsResponse {
  current_period: string;
  current_period_column: string;
  available_periods: Record<string, string>;
  period_display_names?: Record<string, string>; // e.g., {"mar_2025": "Mar-2025"}
}

export interface SetPeriodRequest {
  period_key: string;
}

export interface SetPeriodResponse {
  success: boolean;
  message: string;
  period_key: string;
  period_column: string;
}

export interface AddPeriodRequest {
  period_key: string;
  column_name: string;
}

export interface AddPeriodResponse {
  success: boolean;
  message: string;
  period_key: string;
  column_name: string;
}

interface CompanyWithCategoriesResponse {
  name: string;
  csv_file: string;
  notes_count: number;
  notes: Array<{
    number: string;
    title: string;
  }>;
  categories: Array<{
    id: string;
    name: string;
    description: string;
    notes_count: number;
    notes: Array<{
      number: string;
      title: string;
    }>;
  }>;
}

// Add these interfaces and methods to your existing api.ts file

// ============================================
// PERIOD MANAGEMENT INTERFACES
// ============================================
export interface GetPeriodsResponse {
  current_period: string;
  current_period_column: string;
  available_periods: Record<string, string>;
  period_display_names?: Record<string, string>; // e.g., {"mar_2025": "Mar-2025"}
}

export interface SetPeriodRequest {
  period_key: string;
}

export interface SetPeriodResponse {
  success: boolean;
  message: string;
  period_key: string;
  period_column: string;
}

export interface AddPeriodRequest {
  period_key: string;
  column_name: string;
}

export interface AddPeriodResponse {
  success: boolean;
  message: string;
  period_key: string;
  column_name: string;
}

export interface CashFlowReadinessResponse {
  company_name: string;
  is_ready: boolean;
  markdown_file: string;
  period: string;
  generated_at: string;
  file_size: number;
  message: string;
}

export interface CashFlowTemplateRequest {
  company_name: string;
  period_ended?: string;
}

export interface CashFlowTemplateResponse {
  success: boolean;
  message: string;
  output_file: string;
  company_name: string;
  period_ended: string;
  source_markdown: string;
}


// ============================================
// FINANALYZER P&L API INTERFACES
// ============================================

export interface FinAnalyzerPNLRequest {
  company_name: string;
  period_label?: string;
  entity_info?: string;
  currency?: string;
  scenario?: string;
}

export interface FinAnalyzerPNLResponse {
  success: boolean;
  message: string;
  statement?: {
    company_name: string;
    period_ended: string;
    sections: any[];
    metadata: {
      generated_at: string;
      notes_used: string[];
      type: string;
    };
  };
  output_file?: string;
  html_preview?: string | null;
}

export interface FinAnalyzerFile {
  filename: string;
  file_path: string;
  size_bytes: number;
  generated_at: string;
  download_url: string;
}

export interface FinAnalyzerPNLListResponse {
  company_name: string;
  statements: FinAnalyzerFile[];
  count: number;
  latest: FinAnalyzerFile | null;
}


// ============================================
// FINANALYZER P&L SCHEDULE API INTERFACES
// ============================================

export interface FinAnalyzerPNLScheduleRequest {
  company_name: string;
  period_label?: string;
  entity_info?: string;
  currency?: string;
  scenario?: string;
  show_currency_prefix?: boolean;
  currency_prefix?: string;
  convert_to_lakh?: boolean;
}

export interface FinAnalyzerPNLScheduleResponse {
  success: boolean;
  message: string;
  output_file?: string;
  metadata?: {
    generated_at: string;
    notes_included: string[];
    type: string;
  };
}

export interface FinAnalyzerPNLScheduleListResponse {
  company_name: string;
  schedules: FinAnalyzerFile[];
  count: number;
  latest: FinAnalyzerFile | null;
}

// ============================================
// CASH FLOW FINALYZER API INTERFACES
// ============================================

export interface CashFlowFinalizerRequest {
  company_name: string;
  period_label?: string;
  entity_info?: string;
  currency?: string;
  scenario?: string;
}

export interface CashFlowFinalizerResponse {
  success: boolean;
  message: string;
  output_file?: string;
  company_name?: string;
  period_label?: string;
  items_extracted?: number;
}

export interface CashFlowFinalizerReadinessResponse {
  company_name: string;
  is_ready: boolean;
  markdown_file?: string;
  message: string;
  statement_type?: string;
}

export interface CashFlowFinalizerFile {
  filename: string;
  path: string;
  generated_at: string;
  size: number;
}

export interface CashFlowFinalizerListResponse {
  company_name: string;
  statements: CashFlowFinalizerFile[];
  count: number;
  latest: CashFlowFinalizerFile | null;
}



// ============================================
// BS FINALYZER API INTERFACES
// ============================================

export interface BSFinalizerRequest {
  company_name: string;
  period_label?: string;
  entity_info?: string;
  currency?: string;
  scenario?: string;
}

export interface BSFinalizerResponse {
  success: boolean;
  message: string;
  statement?: {
    company_name: string;
    as_at_date: string;
    sections: any[];
    metadata: {
      generated_at: string;
      notes_used: string[];
      type: string;
    };
  };
  output_file?: string;
}

// ============================================
// BS SCHEDULE API INTERFACES
// ============================================

export interface BSScheduleRequest {
  company_name: string;
  period_label?: string;
  entity_info?: string;
  currency?: string;
  scenario?: string;
  show_currency_prefix?: boolean;
  currency_prefix?: string;
  convert_to_lakh?: boolean;
}

export interface BSScheduleResponse {
  success: boolean;
  message: string;
  output_file?: string;
  metadata?: {
    generated_at: string;
    notes_included: string[];
    type: string;
    periods?: string[];
  };
}

// ============================================
// EQUITY SCHEDULE API INTERFACES
// ============================================

export interface EquityScheduleRequest {
  company_name: string;
  period_label?: string;
  entity_info?: string;
  currency?: string;
  scenario?: string;
  show_currency_prefix?: boolean;
  currency_prefix?: string;
  convert_to_lakh?: boolean;
}

export interface EquityScheduleResponse {
  success: boolean;
  message: string;
  output_file?: string;
  metadata?: {
    generated_at: string;
    notes_included: string[];
    type: string;
    periods?: string[];
  };
}

// ============================================
// BS FINALYZER API SERVICE
// ============================================

class BSFinalizerApiService {
  /**
   * Check if all required notes are available for BS Finalyzer generation
   */
  async checkReadiness(companyName: string): Promise<StatementReadinessResponse> {
    const response = await api.get<StatementReadinessResponse>(
      `/api/bs-finalyzer-readiness/${companyName}`
    );
    return response.data;
  }

  /**
   * Generate BS Finalyzer statement
   */
  async generateBSFinalyzer(request: BSFinalizerRequest): Promise<BSFinalizerResponse> {
    const params = new URLSearchParams();
    params.append('company_name', request.company_name);

    if (request.period_label) {
      params.append('period_label', request.period_label);
    }
    if (request.entity_info) {
      params.append('entity_info', request.entity_info);
    }
    if (request.currency) {
      params.append('currency', request.currency);
    }
    if (request.scenario) {
      params.append('scenario', request.scenario);
    }

    const response = await api.post<BSFinalizerResponse>(
      `/api/generate-bs-finalyzer?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Download latest BS Finalyzer statement
   */
  downloadLatestBSFinalyzer(companyName: string): void {
    const url = `${API_BASE_URL}/api/download-bs-finalyzer/${companyName}`;
    window.open(url, '_blank');
  }

  /**
   * Trigger download in browser
   */
  async triggerBSFinalizerDownload(companyName: string): Promise<void> {
    const url = `${API_BASE_URL}/api/download-bs-finalyzer/${companyName}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `BS_Finalyzer_${companyName}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }
}

// ============================================
// BS SCHEDULE API SERVICE
// ============================================

class BSScheduleApiService {
  /**
   * Check if all required notes are available for BS Schedule generation
   */
  async checkReadiness(companyName: string): Promise<StatementReadinessResponse> {
    const response = await api.get<StatementReadinessResponse>(
      `/api/bs-schedule-readiness/${companyName}`
    );
    return response.data;
  }

  /**
   * Generate BS Schedule
   */
  async generateBSSchedule(request: BSScheduleRequest): Promise<BSScheduleResponse> {
    const params = new URLSearchParams();
    params.append('company_name', request.company_name);

    if (request.period_label) {
      params.append('period_label', request.period_label);
    }
    if (request.entity_info) {
      params.append('entity_info', request.entity_info);
    }
    if (request.currency) {
      params.append('currency', request.currency);
    }
    if (request.scenario) {
      params.append('scenario', request.scenario);
    }
    if (request.show_currency_prefix !== undefined) {
      params.append('show_currency_prefix', request.show_currency_prefix.toString());
    }
    if (request.currency_prefix) {
      params.append('currency_prefix', request.currency_prefix);
    }
    if (request.convert_to_lakh !== undefined) {
      params.append('convert_to_lakh', request.convert_to_lakh.toString());
    }

    const response = await api.post<BSScheduleResponse>(
      `/api/generate-bs-schedule?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Download latest BS Schedule
   */
  downloadLatestBSSchedule(companyName: string): void {
    const url = `${API_BASE_URL}/api/download-bs-schedule/${companyName}`;
    window.open(url, '_blank');
  }

  /**
   * Trigger download in browser
   */
  async triggerBSScheduleDownload(companyName: string): Promise<void> {
    const url = `${API_BASE_URL}/api/download-bs-schedule/${companyName}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `BS_Schedule_${companyName}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }
}

// ============================================
// EQUITY SCHEDULE API SERVICE
// ============================================

class EquityScheduleApiService {
  /**
   * Check if all required notes are available for Equity Schedule generation
   */
  async checkReadiness(companyName: string): Promise<StatementReadinessResponse> {
    const response = await api.get<StatementReadinessResponse>(
      `/api/equity-schedule-readiness/${companyName}`
    );
    return response.data;
  }

  /**
   * Generate Equity Schedule
   */
  async generateEquitySchedule(request: EquityScheduleRequest): Promise<EquityScheduleResponse> {
    const response = await api.post<EquityScheduleResponse>(
      '/api/v1/equity-schedule/generate',
      request
    );
    return response.data;
  }

  /**
   * Download latest Equity Schedule
   */
  downloadLatestEquitySchedule(companyName: string): void {
    const url = `${API_BASE_URL}/api/download-equity-schedule/${companyName}`;
    window.open(url, '_blank');
  }

  /**
   * Trigger download in browser
   */
  async triggerEquityScheduleDownload(companyName: string): Promise<void> {
    const url = `${API_BASE_URL}/api/download-equity-schedule/${companyName}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `Equity_Schedule_${companyName}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }
}

// ============================================
// EXPORT NEW SERVICES
// ============================================

export const bsFinalizerApi = new BSFinalizerApiService();
export const bsScheduleApi = new BSScheduleApiService();
export const equityScheduleApi = new EquityScheduleApiService();
class CashFlowFinalizerApiService {
  /**
   * Check if Cash Flow Statement markdown is ready for Finalyzer generation
   */
  async checkReadiness(companyName: string): Promise<CashFlowFinalizerReadinessResponse> {
    const response = await api.get<CashFlowFinalizerReadinessResponse>(
      `/api/cashflow-finalyzer-readiness/${companyName}`
    );
    return response.data;
  }

  /**
   * Generate Cash Flow Finalyzer statement
   */
  async generateCashFlowFinalyzer(request: CashFlowFinalizerRequest): Promise<CashFlowFinalizerResponse> {
    const params = new URLSearchParams();
    params.append('company_name', request.company_name);

    if (request.period_label) {
      params.append('period_label', request.period_label);
    }
    if (request.entity_info) {
      params.append('entity_info', request.entity_info);
    }
    if (request.currency) {
      params.append('currency', request.currency);
    }
    if (request.scenario) {
      params.append('scenario', request.scenario);
    }

    const response = await api.post<CashFlowFinalizerResponse>(
      `/api/generate-cashflow-finalyzer?${params.toString()}`
    );
    return response.data;
  }

  /**
   * List all generated Cash Flow Finalyzer statements
   */
  async listCashFlowFinalyzers(companyName: string): Promise<CashFlowFinalizerListResponse> {
    const response = await api.get<CashFlowFinalizerListResponse>(
      `/api/cashflow-finalyzer-list/${companyName}`
    );
    return response.data;
  }

  /**
   * Download latest Cash Flow Finalyzer statement
   */
  downloadLatestCashFlowFinalyzer(companyName: string): void {
    const url = `${API_BASE_URL}/api/download-cashflow-finalyzer/${companyName}`;
    window.open(url, '_blank');
  }

  /**
   * Trigger download in browser with proper filename
   */
  async triggerCashFlowFinalizerDownload(companyName: string): Promise<void> {
    const url = `${API_BASE_URL}/api/download-cashflow-finalyzer/${companyName}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `CashFlow_Finalyzer_${companyName}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }

  /**
   * Delete a specific Cash Flow Finalyzer file
   */
  async deleteCashFlowFinalyzer(companyName: string, filename: string): Promise<any> {
    const response = await api.delete(
      `/api/cashflow-finalyzer/${companyName}/${filename}`
    );
    return response.data;
  }
}

// ============================================
// EXPORT CASH FLOW FINALYZER SERVICE
// ============================================

export const cashFlowFinalizerApi = new CashFlowFinalizerApiService();

// ============================================
// FINANALYZER P&L API SERVICE
// ============================================


class FinAnalyzerPNLApiService {
  /**
   * Check if all required notes are available for PNL Finalyzer generation
   */
  async checkReadiness(companyName: string): Promise<StatementReadinessResponse> {
    const response = await api.get<StatementReadinessResponse>(
      `/api/pnl-finalyzer-readiness/${companyName}`
    );
    return response.data;
  }

  /**
   * Generate PNL Finalyzer statement
   */
  async generatePNLFinalyzer(request: FinAnalyzerPNLRequest): Promise<FinAnalyzerPNLResponse> {
    const params = new URLSearchParams();
    params.append('company_name', request.company_name);

    if (request.period_label) {
      params.append('period_label', request.period_label);
    }
    if (request.entity_info) {
      params.append('entity_info', request.entity_info);
    }
    if (request.currency) {
      params.append('currency', request.currency);
    }
    if (request.scenario) {
      params.append('scenario', request.scenario);
    }

    const response = await api.post<FinAnalyzerPNLResponse>(
      `/api/generate-pnl-finalyzer?${params.toString()}`
    );
    return response.data;
  }

  /**
   * List all generated PNL Finalyzer statements
   */
  async listPNLFinalyzers(companyName: string): Promise<FinAnalyzerPNLListResponse> {
    const response = await api.get<FinAnalyzerPNLListResponse>(
      `/api/pnl-finalyzer-list/${companyName}`
    );
    return response.data;
  }

  /**
   * Download latest PNL Finalyzer statement
   */
  downloadLatestPNLFinalyzer(companyName: string): void {
    const url = `${API_BASE_URL}/api/download-pnl-finalyzer/${companyName}`;
    window.open(url, '_blank');
  }

  /**
   * Trigger download in browser
   */
  async triggerPNLFinalyzerDownload(companyName: string): Promise<void> {
    const url = `${API_BASE_URL}/api/download-pnl-finalyzer/${companyName}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `PNL_Finalyzer_${companyName}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }
}

// ============================================
// EXPORT FINANALYZER P&L SERVICE
// ============================================

export const finAnalyzerPNLApi = new FinAnalyzerPNLApiService();


// ============================================
// FINANALYZER P&L SCHEDULE API SERVICE
// ============================================

class FinAnalyzerPNLScheduleApiService {
  /**
   * Check if all required notes are available for PNL Schedule generation
   */
  async checkReadiness(companyName: string): Promise<StatementReadinessResponse> {
    const response = await api.get<StatementReadinessResponse>(
      `/api/pnl-schedule-readiness/${companyName}`
    );
    return response.data;
  }

  /**
   * Generate PNL Schedule Finalyzer
   */
  async generatePNLSchedule(request: FinAnalyzerPNLScheduleRequest): Promise<FinAnalyzerPNLScheduleResponse> {
    const params = new URLSearchParams();
    params.append('company_name', request.company_name);

    if (request.period_label) {
      params.append('period_label', request.period_label);
    }
    if (request.entity_info) {
      params.append('entity_info', request.entity_info);
    }
    if (request.currency) {
      params.append('currency', request.currency);
    }
    if (request.scenario) {
      params.append('scenario', request.scenario);
    }
    if (request.show_currency_prefix !== undefined) {
      params.append('show_currency_prefix', request.show_currency_prefix.toString());
    }
    if (request.currency_prefix) {
      params.append('currency_prefix', request.currency_prefix);
    }
    if (request.convert_to_lakh !== undefined) {
      params.append('convert_to_lakh', request.convert_to_lakh.toString());
    }

    const response = await api.post<FinAnalyzerPNLScheduleResponse>(
      `/api/generate-pnl-schedule?${params.toString()}`
    );
    return response.data;
  }

  /**
   * List all generated PNL Schedules
   */
  async listPNLSchedules(companyName: string): Promise<FinAnalyzerPNLScheduleListResponse> {
    const response = await api.get<FinAnalyzerPNLScheduleListResponse>(
      `/api/pnl-schedule-list/${companyName}`
    );
    return response.data;
  }

  /**
   * Download latest PNL Schedule
   */
  downloadLatestPNLSchedule(companyName: string): void {
    const url = `${API_BASE_URL}/api/download-pnl-schedule/${companyName}`;
    window.open(url, '_blank');
  }

  /**
   * Trigger download in browser
   */
  async triggerPNLScheduleDownload(companyName: string): Promise<void> {
    const url = `${API_BASE_URL}/api/download-pnl-schedule/${companyName}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `PNL_Schedule_${companyName}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }
}

// ============================================
// EXPORT FINANALYZER SERVICES
// ============================================

export const finAnalyzerPNLScheduleApi = new FinAnalyzerPNLScheduleApiService();



// ============================================
// PERIOD MANAGEMENT API METHODS
// ============================================

// Add these methods to your apiService object:

export const periodManagementApi = {
  /**
   * Get current period configuration and available periods
   * GET /api/periods
   */
  getPeriods: async () => {
    const response = await api.get<GetPeriodsResponse>('/api/periods');
    return response;
  },

  /**
   * Set the active period for all note generations
   * POST /api/periods/set
   */
  setPeriod: async (periodKey: string) => {
    const response = await api.post<SetPeriodResponse>('/api/periods/set', {
      period_key: periodKey
    });
    return response;
  },

  /**
   * Add a custom period mapping
   * POST /api/periods/add
   */
  addCustomPeriod: async (periodKey: string, columnName: string) => {
    const response = await api.post<AddPeriodResponse>('/api/periods/add', {
      period_key: periodKey,
      column_name: columnName
    });
    return response;
  },
};

// ============================================
// P&L STATEMENT SERVICE
// ============================================

class PLStatementApiService {
  async checkReadiness(companyName: string, cpmCategory?: string): Promise<StatementReadinessResponse> {
    const url = cpmCategory
      ? `${API_BASE_URL}/api/pl-statement-readiness/${companyName}?cpm_category=${cpmCategory}`
      : `${API_BASE_URL}/api/pl-statement-readiness/${companyName}`;
    const response = await axios.get<StatementReadinessResponse>(url);
    return response.data;
  }

  async generatePLStatement(request: StatementGenerationRequest): Promise<StatementGenerationResponse> {
    const response = await axios.post<StatementGenerationResponse>(
      `${API_BASE_URL}/api/generate-pl-statement`,
      request
    );
    return response.data;
  }

  downloadLatestPLStatement(companyName: string, cpmCategory?: string): void {
    const url = cpmCategory
      ? `${API_BASE_URL}/api/download-pl-statement/${companyName}?cpm_category=${cpmCategory}`
      : `${API_BASE_URL}/api/download-pl-statement/${companyName}`;
    window.open(url, '_blank');
  }

  async listPLStatements(companyName: string, cpmCategory?: string): Promise<any> {
    const url = cpmCategory
      ? `${API_BASE_URL}/api/pl-statements-list/${companyName}?cpm_category=${cpmCategory}`
      : `${API_BASE_URL}/api/pl-statements-list/${companyName}`;
    const response = await axios.get(url);
    return response.data;
  }

  async deletePLStatement(companyName: string, filename: string): Promise<any> {
    const response = await axios.delete(
      `${API_BASE_URL}/api/pl-statement/${companyName}/${filename}`
    );
    return response.data;
  }
}

// ============================================
// CASH FLOW STATEMENT SERVICE
// ============================================

class CashFlowApiService {
  /**
   * Check if Cash Flow Statement markdown file is ready
   * GET /api/cashflow-statement-readiness/{company_name}
   */
  async checkReadiness(companyName: string): Promise<CashFlowReadinessResponse> {
    const url = `${API_BASE_URL}/api/cashflow-statement-readiness/${companyName}`;
    const response = await axios.get<CashFlowReadinessResponse>(url);
    return response.data;
  }

  /**
   * Generate Cash Flow Statement Excel template from markdown
   * POST /api/generate-cashflow-template
   */
  async generateCashFlowTemplate(request: CashFlowTemplateRequest): Promise<CashFlowTemplateResponse> {
    const response = await axios.post<CashFlowTemplateResponse>(
      `${API_BASE_URL}/api/generate-cashflow-template`,
      request,
      {
        timeout: 120000, // 120 seconds for statement generation
      }
    );
    return response.data;
  }

  /**
   * Download the latest Cash Flow Statement Excel file
   * GET /api/download-cashflow-template/{company_name}
   */
  downloadLatestCashFlow(companyName: string): void {
    const url = `${API_BASE_URL}/api/download-cashflow-template/${companyName}`;
    window.open(url, '_blank');
  }

  /**
   * List all Cash Flow statements for a company
   * GET /api/cashflow-statements-list/{company_name}
   */
  async listCashFlowStatements(companyName: string): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/api/cashflow-statements-list/${companyName}`);
    return response.data;
  }

  /**
   * Delete a Cash Flow statement file
   * DELETE /api/cashflow-statement/{company_name}/{filename}
   */
  async deleteCashFlowStatement(companyName: string, filename: string): Promise<any> {
    const response = await axios.delete(`${API_BASE_URL}/api/cashflow-statement/${companyName}/${filename}`);
    return response.data;
  }
}

// Export updated service instance
// export const cashFlowApi = new CashFlowApiService();

// ============================================
// BALANCE SHEET STATEMENT SERVICE
// ============================================

class BalanceSheetApiService {
  async checkReadiness(companyName: string, cpmCategory?: string): Promise<StatementReadinessResponse> {
    const url = cpmCategory
      ? `${API_BASE_URL}/api/bs-statement-readiness/${companyName}?cpm_category=${cpmCategory}`
      : `${API_BASE_URL}/api/bs-statement-readiness/${companyName}`;
    const response = await axios.get<StatementReadinessResponse>(url);
    return response.data;
  }

  async generateBalanceSheet(request: StatementGenerationRequest): Promise<StatementGenerationResponse> {
    const response = await axios.post<StatementGenerationResponse>(
      `${API_BASE_URL}/api/generate-bs-statement`,
      request,
      {
        timeout: 120000, // 120 seconds for statement generation
      }
    );
    return response.data;
  }

  downloadLatestBalanceSheet(companyName: string, cpmCategory?: string): void {
    const url = cpmCategory
      ? `${API_BASE_URL}/api/download-bs-statement/${companyName}?cpm_category=${cpmCategory}`
      : `${API_BASE_URL}/api/download-bs-statement/${companyName}`;
    window.open(url, '_blank');
  }

  async listBalanceSheets(companyName: string, cpmCategory?: string): Promise<any> {
    const url = cpmCategory
      ? `${API_BASE_URL}/api/bs-statements-list/${companyName}?cpm_category=${cpmCategory}`
      : `${API_BASE_URL}/api/bs-statements-list/${companyName}`;
    const response = await axios.get(url);
    return response.data;
  }

  async deleteBalanceSheet(companyName: string, filename: string): Promise<any> {
    const response = await axios.delete(
      `${API_BASE_URL}/api/bs-statement/${companyName}/${filename}`
    );
    return response.data;
  }
}

// ============================================
// EXPORTS FOR STATEMENTS
// ============================================

export const plStatementApi = new PLStatementApiService();
export const cashFlowApi = new CashFlowApiService();
export const balanceSheetApi = new BalanceSheetApiService();

// ============================================
// API INSTANCE
// ============================================

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 seconds (2 minutes) for LLM operations
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      console.error('Unauthorized access');
    }
    return Promise.reject(error);
  }
);

// ============================================
// LEGACY API SERVICE
// ============================================

export const apiService = {
  // ============================================================================
  // NOTE GENERATION API (NEW)
  // ============================================================================
  downloadNoteAsExcel: async (companyName: string, filename: string): Promise<void> => {
    try {
      // Call backend endpoint - note the /api/notes prefix
      const response = await fetch(
        `${API_BASE_URL}/api/notes/generate-and-download-excel/${encodeURIComponent(companyName)}/${encodeURIComponent(filename)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        // Try to get error details from response
        let errorMessage = `Failed to download: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          // If response is not JSON, use status text
        }
        throw new Error(errorMessage);
      }

      // Get the blob from response
      const blob = await response.blob();

      // Extract filename from Content-Disposition header or create default
      const contentDisposition = response.headers.get('Content-Disposition');
      let downloadFilename = 'note.xlsx';

      if (contentDisposition) {
        // Try to extract filename from header
        // Supports both formats: filename="file.xlsx" and filename=file.xlsx
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          downloadFilename = filenameMatch[1].replace(/['"]/g, '');
        }
      } else {
        // Generate filename from the markdown filename
        // Convert "Note_28_Employee_Benefits.md" to "Note_28_Employee_Benefits.xlsx"
        downloadFilename = filename.replace('.md', '.xlsx');
      }

      // Create download link and trigger download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = downloadFilename;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);
    } catch (error) {
      console.error('Error downloading Excel:', error);
      throw error;
    }
  },
  /**
   * Get all companies
   */
  getCompanies: async (): Promise<Company[]> => {
    const response = await api.get<Company[]>('/api/companies');
    return response.data;
  },

  /**
   * Get company details by name
   */
  getCompanyDetails: async (companyName: string): Promise<Company> => {
    const response = await api.get<Company>(`/api/companies/${companyName}`);
    return response.data;
  },

  /**
   * Get company categories
   */
  getCompanyCategories: async (companyName: string): Promise<NoteCategory[]> => {
    const response = await api.get<CompanyWithCategoriesResponse>(
      `/api/companies/${companyName}/categories`,
      {
        timeout: 60000, // 60 seconds timeout for category loading
      }
    );

    return response.data.categories.map(cat => ({
      id: cat.id,
      name: cat.name,
      description: cat.description,
      icon: getCategoryIcon(cat.id),
      color: getCategoryColor(cat.id),
      notes: cat.notes,
    }));
  },


  /**
   * Get company currency information
   */
  getCompanyCurrency: async (companyName: string): Promise<any> => {
    const response = await api.get(`/api/companies/${companyName}/currency`);
    return response.data;
  },

  /**
   * Get currency context with conversion rates
   */
  getCurrencyContext: async (companyName: string, targetCurrencies: string[], forceRefresh: boolean = false): Promise<any> => {
    const response = await api.get(`/api/currency/context/${companyName}`, {
      params: {
        targets: targetCurrencies.join(','),
        force_refresh: forceRefresh
      }
    });
    return response.data;
  },

  /**
   * Generate a single note
   */
  generateNote: async (companyName: string, noteNumber: string): Promise<GenerationResponse> => {
    const response = await api.post<GenerationResponse>('/api/generate', {
      company_name: companyName,
      note_number: noteNumber,
    }, {
      timeout: 120000, // 120 seconds for LLM note generation
    });
    return response.data;
  },

  /**
   * Start batch generation
   */
  generateBatch: async (companyName: string, categoryId?: string): Promise<any> => {
    const response = await api.post<any>('/api/generate/batch', {
      company_name: companyName,
      category_id: categoryId,
    }, {
      timeout: 120000, // 120 seconds for batch generation
    });
    return response.data;
  },

  /**
   * Get batch generation status
   */
  getBatchStatus: async (batchId: string): Promise<BatchStatus> => {
    const response = await api.get<BatchStatus>(`/api/generate/batch/${batchId}/status`, {
      timeout: 10000, // 10 seconds timeout for status checks
    });
    return response.data;
  },

  // ============================================================================
  // P&L STATEMENT API
  // ============================================================================

  /**
   * Check P&L statement readiness
   */
  checkPLReadiness: async (companyName: string): Promise<PLReadinessResponse> => {
    const response = await api.get<PLReadinessResponse>(
      `/api/pl-statement-readiness/${companyName}`
    );
    return response.data;
  },

  /**
   * Generate P&L statement
   */
  generatePLStatement: async (request: PLGenerationRequest): Promise<PLGenerationResponse> => {
    const response = await api.post<PLGenerationResponse>(
      '/api/generate-pl-statement',
      request,
      {
        timeout: 120000, // 120 seconds for statement generation
      }
    );
    return response.data;
  },

  /**
   * List all P&L statements
   */
  listPLStatements: async (companyName: string): Promise<PLStatementsListResponse> => {
    const response = await api.get<PLStatementsListResponse>(
      `/api/pl-statements-list/${companyName}`
    );
    return response.data;
  },

  /**
   * Download P&L statement
   */
  downloadPLStatement: (companyName: string, filename?: string): string => {
    const url = filename
      ? `/api/download-pl-statement/${companyName}?filename=${encodeURIComponent(filename)}`
      : `/api/download-pl-statement/${companyName}`;

    return `${API_BASE_URL}${url}`;
  },

  /**
   * Trigger download in browser
   */
  triggerPLStatementDownload: async (companyName: string, filename?: string): Promise<void> => {
    const url = apiService.downloadPLStatement(companyName, filename);

    try {
      const response = await fetch(url, {
        headers: {
          // Add any auth headers here if needed
        },
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || `PL_Statement_${companyName}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  },

  /**
   * Delete a P&L statement file
   */
  deletePLStatement: async (companyName: string, filename: string): Promise<any> => {
    const response = await api.delete(`/api/pl-statement/${companyName}/${filename}`);
    return response.data;
  },

  // ============================================================================
  // GENERATED NOTES API
  // ============================================================================

  /**
   * List generated notes for a company, optionally filtered by category
   */
  listGeneratedNotes: async (
    companyName: string,
    categoryId?: string
  ): Promise<GeneratedNotesListResponse> => {
    const url = categoryId
      ? `/api/generated-notes/${companyName}?category_id=${categoryId}`
      : `/api/generated-notes/${companyName}`;
    const response = await api.get<GeneratedNotesListResponse>(url);
    return response.data;
  },

  /**
   * Get note content
   */
  getNoteContent: async (companyName: string, filename: string): Promise<NoteContentResponse> => {
    const response = await api.get<NoteContentResponse>(
      `/api/note-content/${companyName}/${filename}`
    );
    return response.data;
  },

  /**
   * Trigger note download in browser
   */
  triggerNoteDownload: async (companyName: string, filename: string): Promise<void> => {
    const url = `${API_BASE_URL}/api/download-note/${companyName}/${filename}`;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  },

  // ============================================================================
  // LEGACY WORKFLOW API
  // ============================================================================

  // Health and system
  getHealth: () => api.get<HealthStatus>('/api/health'),
  getEntities: () => api.get<EntityInfo[]>('/api/entities'),

  // File uploads
  uploadTrialBalance: (entity: string, file: File) => {
    const formData = new FormData();
    formData.append('entity', entity);
    formData.append('file', file);
    return api.post('/api/upload/trial-balance', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  uploadConfigFile: (entity: string, file: File) => {
    const formData = new FormData();
    formData.append('entity', entity);
    formData.append('file', file);
    return api.post('/api/upload/config', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  uploadAdjustments: (entity: string, files: File[]) => {
    const formData = new FormData();
    formData.append('entity', entity);
    files.forEach(file => {
      formData.append('files', file);
    });
    return api.post('/api/upload/adjustments', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Processing
  processAdjustments: (entity: string, opts?: { periodKey?: string; periodColumn?: string }) => {
    const formData = new FormData();
    formData.append('entity', entity);
    if (opts?.periodKey) formData.append('period_key', opts.periodKey);
    if (opts?.periodColumn) formData.append('period_column', opts.periodColumn);
    return api.post('/api/process/adjustments', formData);
  },

  getProcessingStatus: (processingId: string) =>
    api.get<ProcessingStatus>(`/api/process/status/${processingId}`),

  // Get detailed adjustment information after processing
  getAdjustmentDetails: (processingId: string) =>
    api.get(`/api/adjustments/details/${processingId}`),

  // Get adjustment summary by entity (no processing ID required)
  getAdjustmentSummary: (entity: string) =>
    api.get(`/api/adjustments/summary/${entity}`),

  // Analyze adjustments with industry-standard classifications
  analyzeAdjustments: (entity: string, period?: string) =>
    api.get(`/api/adjustments/analyze/${entity}`, {
      params: period ? { period } : undefined
    }),

  // Preview adjustment file
  previewAdjustmentFile: (entity: string, filename: string, rows: number = 50) =>
    api.get(`/api/adjustments/preview/${entity}/${filename}`, {
      params: { rows }
    }),

  // Download adjustment file
  downloadAdjustmentFile: (entity: string, filename: string) =>
    api.get(`/api/adjustments/download/${entity}/${filename}`, {
      responseType: 'blob'
    }),

  // Validation
  getValidationRulesConfig: (entity: string) =>
    api.get(`/api/validation/rules/${entity}`),

  validate6Rules: (entity: string) => {
    const formData = new FormData();
    formData.append('entity', entity);
    return api.post('/api/validate/6-rules', formData);
  },

  // Validate with custom rule overrides (toggle support)
  validate6RulesWithOverrides: (entity: string, ruleOverrides?: { [key: string]: boolean }) => {
    const formData = new FormData();
    formData.append('entity', entity);
    if (ruleOverrides) {
      formData.append('rule_overrides', JSON.stringify(ruleOverrides));
    }
    return api.post('/api/validate/6-rules', formData);
  },

  // Generate AI insights for validation failures
  generateValidationInsights: (entity: string) => {
    const formData = new FormData();
    formData.append('entity', entity);
    return api.post('/api/validate/generate-insights', formData, {
      timeout: 60000, // 60 seconds for AI generation
    });
  },

  // AI Insights
  generateAIInsights: (validationResult: any, entity: string) => {
    return api.post('/api/ai/insights', {
      validation_result: validationResult,
      entity: entity
    });
  },

  // Feedback
  submitFeedback: (data: any) => {
    return api.post('/api/feedback', data);
  },

  // Mapping
  mapCategories: (entity: string) => {
    const formData = new FormData();
    formData.append('entity', entity);
    return api.post('/api/map-categories', formData);
  },

  // Start category mapping (Step 4)
  startCategoryMapping: (entity: string) =>
    api.post(`/api/mapping/start/${entity}`),

  // Get mapping reference info
  getMappingReference: (entity: string) =>
    api.get(`/api/mapping/reference/${entity}`),

  // Download mapped file
  downloadMappingFile: (entity: string, filename: string) =>
    api.get(`/api/mapping/download/${entity}/${filename}`, {
      responseType: 'blob'
    }),

  // File downloads
  downloadFile: (fileType: string, entity: string) =>
    api.get(`/api/download/${fileType}?entity=${entity}`, {
      responseType: 'blob',
    }),

  // File management
  listEntityFiles: (entity: string) =>
    api.get(`/api/files/${entity}`),

  checkFileExists: (entity: string, folderType: string, filename: string) =>
    api.get(`/api/files/${entity}/check`, {
      params: { folder_type: folderType, filename }
    }),

  downloadEntityFile: (entity: string, folderType: string, filename: string) =>
    api.get(`/api/files/${entity}/download`, {
      params: { folder_type: folderType, filename },
      responseType: 'blob'
    }),

  deleteFile: (entity: string, folderType: string, filename: string) =>
    api.delete(`/api/files/${entity}`, {
      params: { folder_type: folderType, filename }
    }),

  previewFile: (entity: string, folderType: string, filename: string) =>
    api.get(`/api/files/${entity}/preview`, {
      params: { folder_type: folderType, filename }
    }),

  // Legacy Financial statements
  generateNotes: (entity: string, noteTypes: string[]) => {
    const formData = new FormData();
    formData.append('entity', entity);
    noteTypes.forEach(type => formData.append('note_types', type));
    return api.post('/api/generate/notes', formData);
  },

  generateStatements: (entity: string, statementTypes: string[]) => {
    const formData = new FormData();
    formData.append('entity', entity);
    statementTypes.forEach(type => formData.append('statement_types', type));
    return api.post('/api/generate/statements', formData);
  },
  getPeriods: (entity?: string) =>
    api.get('/api/periods', { params: entity ? { entity } : {} }),
  setPeriod: (periodKey: string) =>
    api.post('/api/periods/set', { period_key: periodKey }),
  addCustomPeriod: (periodKey: string, columnName: string) =>
    api.post('/api/periods/add', {
      period_key: periodKey,
      column_name: columnName
    }),

  // ============================================================================
  // ADJUSTMENTS ANALYSIS API
  // ============================================================================

  getAdjustmentsAnalysis: (entity: string, period?: string) =>
    api.get(`/api/adjustments/analyze/${entity}`, {
      params: period ? { period } : {}
    }),

  getAdjustmentImpactSummary: (entity: string) =>
    api.get(`/api/adjustments/impact-summary/${entity}`),

  getFinalTBSummary: (entity: string) =>
    api.get(`/api/adjustments/final-tb-summary/${entity}`),


  // ============================================================================
  // SAP INTEGRATION API
  // ============================================================================

  checkSAPConnectivity: (entity: string) =>
    api.get(`/api/sap/check-connectivity/${entity}`),

  extractTrialBalanceFromSAP: (entity: string, startDate?: string, endDate?: string) =>
    api.post('/api/sap/extract-trial-balance', {
      entity,
      start_date: startDate,
      end_date: endDate
    }),

  getSAPEntities: () =>
    api.get('/api/sap/entities'),

  // ============================================================================
  // STATEMENT VIEWER API
  // ============================================================================

  /**
   * Get statement data for viewer from latest generated Excel file
   * @param statementType - Type of statement ('pl', 'bs', 'cf')
   * @param companyName - Name of the company
   * @returns Statement data with row values
   */
  getStatementData: async (statementType: string, companyName: string) => {
    const response = await api.get(`/api/statement-data/${statementType}/${companyName}`);
    return response.data;
  },

  /**
   * Check which statements are available for a company
   * @param companyName - Name of the company
   * @returns Availability status for each statement type
   */
  checkStatementAvailability: async (companyName: string) => {
    const response = await api.get(`/api/statement-availability/${companyName}`);
    return response.data;
  },
};



// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get category icon
 */
function getCategoryIcon(categoryId: string): string {
  const icons: { [key: string]: string } = {
    'profit-loss': '💰',
    'balance-sheet': '📊',
    'cash-flow': '💵',
  };
  return icons[categoryId] || '📄';
}

/**
 * Get category color
 */
function getCategoryColor(categoryId: string): string {
  const colors: { [key: string]: string } = {
    'profit-loss': 'from-green-500 to-green-600',
    'balance-sheet': 'from-blue-500 to-blue-600',
    'cash-flow': 'from-purple-500 to-purple-600',
  };
  return colors[categoryId] || 'from-gray-500 to-gray-600';
}

/*
  // ============================================================================
  // PERIOD MANAGEMENT API
  // ============================================================================

  getPeriods: () => api.get('/api/periods'),
  
  setPeriod: (periodKey: string) => 
    api.post('/api/periods/set', { period_key: periodKey }),
  
  addCustomPeriod: (periodKey: string, columnName: string) => 
    api.post('/api/periods/add', { 
      period_key: periodKey, 
      column_name: columnName 
    }),
*/


// ============================================
// DEFAULT EXPORT
// ============================================

const defaultExport = {
  plStatement: plStatementApi,
  cashFlow: cashFlowApi,
  balanceSheet: balanceSheetApi,
  finAnalyzerPNL: finAnalyzerPNLApi,
  finAnalyzerPNLSchedule: finAnalyzerPNLScheduleApi,
  cashFlowFinalizer: cashFlowFinalizerApi,
  bsFinalizer: bsFinalizerApi,
  bsSchedule: bsScheduleApi,
  equitySchedule: equityScheduleApi,
  legacy: apiService
};

export default defaultExport;

export { api };
