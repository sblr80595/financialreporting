/**
 * Utility functions for handling note tables
 * Converts markdown tables to structured data and Excel format
 */

import * as XLSX from 'xlsx';

export interface TableData {
  headers: string[];
  rows: string[][];
}

/**
 * Parse markdown content to extract tables
 */
export function parseMarkdownTables(markdown: string): TableData[] {
  const tables: TableData[] = [];
  const lines = markdown.split('\n');
  
  let i = 0;
  while (i < lines.length) {
    const line = lines[i].trim();
    
    // Check if line contains table delimiter (|)
    if (line.includes('|')) {
      const headers: string[] = [];
      const rows: string[][] = [];
      
      // Parse header row
      const headerCells = line.split('|')
        .map(cell => cell.trim())
        .filter(cell => cell.length > 0);
      
      if (headerCells.length > 0) {
        headers.push(...headerCells);
        i++;
        
        // Skip separator line (|---|---|)
        if (i < lines.length && lines[i].includes('---')) {
          i++;
        }
        
        // Parse data rows
        while (i < lines.length) {
          const dataLine = lines[i].trim();
          if (!dataLine.includes('|')) break;
          
          const cells = dataLine.split('|')
            .map(cell => cell.trim())
            .filter((cell, index, arr) => {
              // Filter out empty cells at start/end
              if (index === 0 || index === arr.length - 1) {
                return cell.length > 0;
              }
              return true;
            });
          
          if (cells.length > 0) {
            rows.push(cells);
          }
          i++;
        }
        
        if (headers.length > 0 && rows.length > 0) {
          tables.push({ headers, rows });
        }
      }
    }
    i++;
  }
  
  return tables;
}

/**
 * Sanitize sheet name to remove invalid Excel characters
 * Excel sheet names cannot contain: : \ / ? * [ ]
 * Also limit to 31 characters (Excel's max sheet name length)
 */
function sanitizeSheetName(name: string): string {
  // Remove invalid characters
  let sanitized = name.replace(/[:/\\?*[\]]/g, '_');
  
  // Limit to 31 characters (Excel's max sheet name length)
  if (sanitized.length > 31) {
    sanitized = sanitized.substring(0, 31);
  }
  
  // Remove leading/trailing spaces
  sanitized = sanitized.trim();
  
  // Ensure name is not empty
  if (sanitized.length === 0) {
    sanitized = 'Sheet';
  }
  
  return sanitized;
}

/**
 * Convert table data to Excel and trigger download
 */
export function downloadAsExcel(
  tables: TableData[],
  filename: string,
  sheetNames?: string[]
) {
  const workbook = XLSX.utils.book_new();
  
  tables.forEach((table, index) => {
    const rawSheetName = sheetNames?.[index] || `Sheet${index + 1}`;
    const sheetName = sanitizeSheetName(rawSheetName);
    
    // Combine headers and rows
    const wsData = [table.headers, ...table.rows];
    
    // Create worksheet
    const worksheet = XLSX.utils.aoa_to_sheet(wsData);
    
    // Auto-size columns
    const colWidths = table.headers.map((header, colIndex) => {
      const headerLen = header.length;
      const maxDataLen = Math.max(
        ...table.rows.map(row => (row[colIndex] || '').toString().length)
      );
      return { wch: Math.max(headerLen, maxDataLen, 10) };
    });
    worksheet['!cols'] = colWidths;
    
    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
  });
  
  // Generate Excel file and download
  XLSX.writeFile(workbook, `${filename}.xlsx`);
}

/**
 * Format note number to filename
 */
export function formatNoteFileName(noteNumber: string, noteName?: string, companyName?: string): string {
  const sanitizedNoteNumber = noteNumber.replace(/[^a-zA-Z0-9]/g, '_');
  const timestamp = new Date().toISOString().split('T')[0];
  
  const parts = [companyName, 'Note', sanitizedNoteNumber];
  
  if (noteName) {
    const sanitizedNoteName = noteName.replace(/[^a-zA-Z0-9\s]/g, '').replace(/\s+/g, '_');
    parts.push(sanitizedNoteName);
  }
  
  parts.push(timestamp);
  
  return parts.filter(Boolean).join('_');
}
