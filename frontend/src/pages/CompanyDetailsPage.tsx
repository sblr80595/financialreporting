// src/pages/CompanyDetailsPage.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { ArrowPathIcon, ArrowLeftIcon, EyeIcon, ArrowDownTrayIcon, ClockIcon } from '@heroicons/react/24/outline';
import { Company, GenerationStatusMap, NoteCategory, GeneratedNoteFile } from '../types';
import NoteCard from '../components/NoteCard';
import NoteViewer from '../components/NoteViewer';
import TableNoteViewer from '../components/TableNoteViewer';
import { parseMarkdownTables, downloadAsExcel, formatNoteFileName } from '../utils/noteTableUtils';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';

interface CompanyDetailsPageProps {
  company: Company;
  category: NoteCategory;
  generationStatus: GenerationStatusMap;
  onGenerateNote: (noteNumber: string) => void;
  onGenerateAll: () => void;
  onBack: () => void;
  batchLoading?: boolean;
  hideHeader?: boolean; // New optional prop to hide the header
}

const CompanyDetailsPage: React.FC<CompanyDetailsPageProps> = ({
  company,
  category,
  generationStatus,
  onGenerateNote,
  onGenerateAll,
  onBack,
  batchLoading = false,
  hideHeader = false, // Default to false for backward compatibility
}) => {
  const categoryNotes = category.notes;
  const [generatedNotes, setGeneratedNotes] = useState<GeneratedNoteFile[]>([]);
  const [viewingNote, setViewingNote] = useState<GeneratedNoteFile | null>(null);
  const [viewingNoteContent, setViewingNoteContent] = useState<string>('');
  const [loadingNoteContent, setLoadingNoteContent] = useState(false);

  // All notes now use table viewer for consistent tabular display and Excel export
  const USE_TABLE_VIEWER_FOR_ALL = true;

  // Fetch generated notes for this category
  const fetchGeneratedNotes = useCallback(async () => {
    try {
      const response = await apiService.listGeneratedNotes(company.name, category.id);
      setGeneratedNotes(response.notes);
    } catch (err) {
      console.error('Error loading generated notes:', err);
    }
  }, [company.name, category.id]);

  useEffect(() => {
    fetchGeneratedNotes();
  }, [fetchGeneratedNotes]);

  // Refresh notes when generation status changes
  useEffect(() => {
    const hasSuccess = Object.values(generationStatus).some(status => status === 'success');
    if (hasSuccess) {
      // Delay to allow file to be written
      setTimeout(() => {
        fetchGeneratedNotes();
      }, 1000);
    }
  }, [generationStatus, fetchGeneratedNotes]);

  const handleDownload = async (note: GeneratedNoteFile) => {
    try {
      // Load note content and download as Excel
      const response = await apiService.getNoteContent(company.name, note.filename);
      const content = response.content || '';
      
      // Parse tables from markdown content
      const tables = parseMarkdownTables(content);
      
      if (tables.length === 0) {
        toast.error('No tables found in note to export');
        return;
      }
      
      // Generate Excel filename
      const filename = formatNoteFileName(note.note_number || '', note.title || '', company.name);
      
      // Generate sheet names
      const sheetNames = tables.map((_, index) => 
        note.title ? `${note.title.substring(0, 25)}_${index + 1}` : `Table_${index + 1}`
      );
      
      // Download as Excel
      downloadAsExcel(tables, filename, sheetNames);
      toast.success('Note downloaded as Excel successfully');
    } catch (err) {
      toast.error('Failed to download note');
      console.error('Error downloading note:', err);
    }
  };

  const handleViewNote = async (note: GeneratedNoteFile) => {
    // All notes now use table viewer for consistent experience
    if (USE_TABLE_VIEWER_FOR_ALL) {
      // Load note content for table viewer
      setLoadingNoteContent(true);
      try {
        const response = await apiService.getNoteContent(company.name, note.filename);
        setViewingNoteContent(response.content || '');
        setViewingNote(note);
      } catch (err) {
        toast.error('Failed to load note content');
        console.error('Error loading note content:', err);
      } finally {
        setLoadingNoteContent(false);
      }
    } else {
      // Use regular viewer (fallback - not currently used)
      setViewingNote(note);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Group generated notes by note number
  const groupedNotes = generatedNotes.reduce((acc, note) => {
    const noteNum = note.note_number || 'unknown';
    if (!acc[noteNum]) {
      acc[noteNum] = [];
    }
    acc[noteNum].push(note);
    return acc;
  }, {} as Record<string, GeneratedNoteFile[]>);

  return (
    <div className="mx-auto px-6 py-8">
      {/* Company Header - conditionally shown */}
      {!hideHeader && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors font-satoshi"
              >
                <ArrowLeftIcon className="w-5 h-5" />
                <span className="font-medium">Back</span>
              </button>
              <div className="border-l border-gray-300 pl-4">
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="text-2xl font-bold text-gray-900 font-satoshi">
                    {company.name}
                  </h2>
                  <span className="text-2xl">{category.icon}</span>
                </div>
                <p className="text-gray-600 text-sm font-satoshi">
                  {category.name} • {categoryNotes.length} notes available
                </p>
              </div>
            </div>
            <button
              onClick={onGenerateAll}
              disabled={batchLoading || categoryNotes.length === 0}
              className="flex items-center gap-2 px-6 py-3 rounded-md transition-all font-medium shadow-sm text-white font-satoshi"
              style={{
                backgroundColor: batchLoading || categoryNotes.length === 0 ? '#9ca3af' : PLAINFLOW_RED,
                cursor: batchLoading || categoryNotes.length === 0 ? 'not-allowed' : 'pointer'
              }}
              onMouseEnter={(e) => {
                if (!batchLoading && categoryNotes.length > 0) {
                  e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER;
                }
              }}
              onMouseLeave={(e) => {
                if (!batchLoading && categoryNotes.length > 0) {
                  e.currentTarget.style.backgroundColor = PLAINFLOW_RED;
                }
              }}
            >
              {batchLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Starting Batch...
                </>
              ) : (
                <>
                  <ArrowPathIcon className="w-5 h-5" />
                  Generate All Notes
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Generate All button for tabbed view */}
      {hideHeader && (
        <div className="flex justify-end mb-6 px-6">
          <button
            onClick={onGenerateAll}
            disabled={batchLoading || categoryNotes.length === 0}
            className="flex items-center gap-2 px-6 py-3 rounded-md transition-all font-medium shadow-sm text-white font-satoshi"
            style={{
              backgroundColor: batchLoading || categoryNotes.length === 0 ? '#9ca3af' : PLAINFLOW_RED,
              cursor: batchLoading || categoryNotes.length === 0 ? 'not-allowed' : 'pointer'
            }}
            onMouseEnter={(e) => {
              if (!batchLoading && categoryNotes.length > 0) {
                e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER;
              }
            }}
            onMouseLeave={(e) => {
              if (!batchLoading && categoryNotes.length > 0) {
                e.currentTarget.style.backgroundColor = PLAINFLOW_RED;
              }
            }}
          >
            {batchLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Starting Batch...
              </>
            ) : (
              <>
                <ArrowPathIcon className="w-5 h-5" />
                Generate All Notes
              </>
            )}
          </button>
        </div>
      )}

      {/* Notes Grid */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gray-900 font-satoshi">
          {category.name} Notes
        </h3>
        <p className="text-gray-600 text-sm mt-1 font-satoshi">
          {category.description}
        </p>
      </div>

      {categoryNotes.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <p className="text-gray-600 font-satoshi">No notes available for this category.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {categoryNotes.map((note) => {
            const noteGeneratedFiles = groupedNotes[note.number] || [];
            const latestGenerated = noteGeneratedFiles.length > 0 ? noteGeneratedFiles[0] : null;
            
            return (
              <div key={note.number} className="flex flex-col gap-3">
                <NoteCard
                  noteNumber={note.number}
                  noteTitle={note.title}
                  status={generationStatus[note.number] || 'idle'}
                  onGenerate={onGenerateNote}
                />
                
                {/* Show latest generated note info */}
                {latestGenerated && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <ClockIcon className="w-4 h-4 text-green-700" />
                      <span className="text-xs font-medium text-green-700 font-satoshi">
                        Last Generated
                      </span>
                    </div>
                    <p className="text-xs text-green-600 mb-3 font-satoshi">
                      {formatDate(latestGenerated.generated_at)}
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewNote(latestGenerated)}
                        disabled={loadingNoteContent}
                        className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-white border border-green-300 text-green-700 rounded-md hover:bg-green-100 transition-colors text-xs font-medium font-satoshi disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {loadingNoteContent && viewingNote?.filename === latestGenerated.filename ? (
                          <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-green-700"></div>
                        ) : (
                          <EyeIcon className="w-3.5 h-3.5" />
                        )}
                        View
                      </button>
                      <button
                        onClick={() => handleDownload(latestGenerated)}
                        className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-white border border-green-300 text-green-700 rounded-md hover:bg-green-100 transition-colors text-xs font-medium font-satoshi"
                      >
                        <ArrowDownTrayIcon className="w-3.5 h-3.5" />
                        Download
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Note Viewer Modals */}
      {viewingNote && USE_TABLE_VIEWER_FOR_ALL ? (
        <TableNoteViewer
          noteNumber={viewingNote.note_number || ''}
          noteName={viewingNote.title || ''}
          content={viewingNoteContent}
          companyName={company.name}
          onClose={() => {
            setViewingNote(null);
            setViewingNoteContent('');
          }}
        />
      ) : viewingNote ? (
        <NoteViewer
          companyName={company.name}
          filename={viewingNote.filename}
          noteNumber={viewingNote.note_number}
          title={viewingNote.title}
          onClose={() => setViewingNote(null)}
        />
      ) : null}
    </div>
  );
};

export default CompanyDetailsPage;