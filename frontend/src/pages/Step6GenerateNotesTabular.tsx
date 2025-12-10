import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';
import { NoteCategory, GenerationStatusMap, GenerationResponse, BatchStatus, GeneratedNoteFile } from '../types';
import { useEntity } from '../contexts/EntityContext';
import { ArrowPathIcon, EyeIcon, ArrowDownTrayIcon, ClockIcon } from '@heroicons/react/24/outline';
import GeneratedNoteDisplay from '../components/GeneratedNoteDisplay';
import BatchProgress from '../components/BatchProgress';
import TableNoteViewer from '../components/TableNoteViewer';
import { parseMarkdownTables, downloadAsExcel, formatNoteFileName } from '../utils/noteTableUtils';

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';

const Step6GenerateNotesTabular: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();
  const companyName = getCompanyName();

  // Note generation state
  const [availableCategories, setAvailableCategories] = useState<NoteCategory[]>([]);
  const [generationStatus, setGenerationStatus] = useState<GenerationStatusMap>({});
  const [generatedNote, setGeneratedNote] = useState<GenerationResponse | null>(null);
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const [activeTab, setActiveTab] = useState<string>('');
  const [generatedNotes, setGeneratedNotes] = useState<Record<string, GeneratedNoteFile[]>>({});
  const [viewingNote, setViewingNote] = useState<GeneratedNoteFile | null>(null);
  const [viewingNoteContent, setViewingNoteContent] = useState<string>('');
  const [loadingNoteContent, setLoadingNoteContent] = useState(false);

  const loadCategories = useCallback(async (attempt = 0) => {
    try {
      setLoading(true);
      const categories = await apiService.getCompanyCategories(companyName);
      setAvailableCategories(categories);
      if (categories.length > 0 && !activeTab) {
        setActiveTab(categories[0].id);
      }
      setRetryCount(0);
      setLoading(false);
    } catch (err: any) {
      console.error('Error loading categories:', err);
      
      if (attempt < 3) {
        const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
        toast.error(`Loading categories... Retrying in ${delay/1000}s`);
        setTimeout(() => {
          setRetryCount(attempt + 1);
          loadCategories(attempt + 1);
        }, delay);
      } else {
        const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to load categories';
        toast.error(`${errorMsg}. Please refresh the page.`);
        setLoading(false);
      }
    }
  }, [companyName, activeTab]);

  // Fetch generated notes for all categories
  const fetchGeneratedNotes = useCallback(async () => {
    try {
      const notesMap: Record<string, GeneratedNoteFile[]> = {};
      
      for (const category of availableCategories) {
        const response = await apiService.listGeneratedNotes(companyName, category.id);
        
        notesMap[category.id] = response.notes;
      }
      
      setGeneratedNotes(notesMap);
    } catch (err) {
      console.error('Error loading generated notes:', err);
    }
  }, [companyName, availableCategories]);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    if (availableCategories.length > 0) {
      fetchGeneratedNotes();
    }
  }, [availableCategories, fetchGeneratedNotes]);

  // Poll batch status
  useEffect(() => {
    let interval: NodeJS.Timeout;
    let consecutiveErrors = 0;
    const maxConsecutiveErrors = 5;
    
    if (batchId && (batchStatus?.status === 'running' || batchStatus?.status === 'pending')) {
      interval = setInterval(async () => {
        try {
          const status = await apiService.getBatchStatus(batchId);
          setBatchStatus(status);
          consecutiveErrors = 0;
          
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(interval);
            loadCategories();
            fetchGeneratedNotes();
            
            if (status.status === 'completed') {
              const successCount = status.results.filter(r => r.success).length;
              const failCount = status.results.filter(r => !r.success).length;
              
              if (failCount === 0) {
                toast.success(`✅ All ${successCount} notes generated successfully!`);
              } else {
                toast.success(`Batch completed: ${successCount} succeeded, ${failCount} failed`);
              }
            } else {
              toast.error('Batch generation encountered errors. Check the progress modal for details.');
            }
          }
        } catch (err: any) {
          consecutiveErrors++;
          console.error(`Error fetching batch status (attempt ${consecutiveErrors}):`, err);
          
          if (consecutiveErrors >= maxConsecutiveErrors) {
            clearInterval(interval);
            toast.error('Lost connection to batch generation. Please check the backend logs.');
          }
        }
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [batchId, batchStatus?.status, loadCategories, fetchGeneratedNotes]);

  // Generate a single note
  const handleGenerateNote = async (noteNumber: string) => {
    setGenerationStatus(prev => ({ ...prev, [noteNumber]: 'loading' }));
    
    try {
      const result = await apiService.generateNote(companyName, noteNumber);
      setGenerationStatus(prev => ({ ...prev, [noteNumber]: 'success' }));
      setGeneratedNote(result);
      toast.success(`Note ${noteNumber} generated successfully!`);
      
      // Refresh notes after a delay
      setTimeout(() => {
        fetchGeneratedNotes();
      }, 1000);
    } catch (err) {
      setGenerationStatus(prev => ({ ...prev, [noteNumber]: 'error' }));
      toast.error(`Failed to generate Note ${noteNumber}`);
      console.error('Error generating note:', err);
    }
  };

  // Generate all notes in a category (batch)
  const handleGenerateAll = async (categoryId: string) => {
    setBatchLoading(true);

    try {
      const response = await apiService.generateBatch(companyName, categoryId);
      setBatchId(response.batch_id);
      
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const initialStatus = await apiService.getBatchStatus(response.batch_id);
      setBatchStatus(initialStatus);
      
      toast.success(`🚀 Batch generation started! Generating ${initialStatus.total_notes} notes...`, {
        duration: 4000
      });
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to start batch generation';
      toast.error(errorMsg);
      console.error('Error starting batch generation:', err);
    } finally {
      setBatchLoading(false);
    }
  };

  const handleViewNote = async (note: GeneratedNoteFile) => {
    setLoadingNoteContent(true);
    try {
      const response = await apiService.getNoteContent(companyName, note.filename);
      setViewingNoteContent(response.content || '');
      setViewingNote(note);
    } catch (err) {
      toast.error('Failed to load note content');
      console.error('Error loading note content:', err);
    } finally {
      setLoadingNoteContent(false);
    }
  };

  const handleDownload = async (note: GeneratedNoteFile) => {
    try {
      const response = await apiService.getNoteContent(companyName, note.filename);
      const content = response.content || '';
      
      const tables = parseMarkdownTables(content);
      
      if (tables.length === 0) {
        toast.error('No tables found in note to export');
        return;
      }
      
      const filename = formatNoteFileName(note.note_number || '', note.title || '', companyName);
      
      const sheetNames = tables.map((_, index) => 
        note.title ? `${note.title.substring(0, 25)}_${index + 1}` : `Table_${index + 1}`
      );
      
      downloadAsExcel(tables, filename, sheetNames);
      toast.success('Note downloaded as Excel successfully');
    } catch (err) {
      toast.error('Failed to download note');
      console.error('Error downloading note:', err);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="card text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          {retryCount > 0 && (
            <p className="text-sm text-gray-500 mt-2">Retry attempt {retryCount}/3</p>
          )}
        </div>
      </div>
    );
  }

  const activeCategory = availableCategories.find(cat => cat.id === activeTab);

  // Get generated notes for active category grouped by note number
  const categoryGeneratedNotes = generatedNotes[activeTab] || [];
  const groupedNotes = categoryGeneratedNotes.reduce((acc, note) => {
    const noteNum = note.note_number || 'unknown';
    if (!acc[noteNum]) {
      acc[noteNum] = [];
    }
    acc[noteNum].push(note);
    return acc;
  }, {} as Record<string, GeneratedNoteFile[]>);

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="bg-white rounded-t-lg border border-b-0 border-gray-200 shadow-sm">
        <div className="flex overflow-x-auto">
          {availableCategories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveTab(category.id)}
              className={`
                relative px-6 py-4 font-semibold font-satoshi transition-all whitespace-nowrap
                flex items-center gap-3 min-w-fit
                ${activeTab === category.id
                  ? 'text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }
              `}
              style={{
                background: activeTab === category.id 
                  ? `linear-gradient(to right, ${PLAINFLOW_RED}, ${PLAINFLOW_RED_HOVER})` 
                  : 'transparent',
                borderBottom: activeTab === category.id ? 'none' : '2px solid transparent',
              }}
            >
              <span className="text-2xl">{category.icon}</span>
              <div className="text-left">
                <div className="text-sm font-bold">{category.name}</div>
                <div className={`text-xs ${activeTab === category.id ? 'text-white text-opacity-90' : 'text-gray-500'}`}>
                  {category.notes.length} {category.notes.length === 1 ? 'Note' : 'Notes'}
                </div>
              </div>
              {activeTab === category.id && (
                <div 
                  className="absolute bottom-0 left-0 right-0 h-1"
                  style={{ background: PLAINFLOW_RED }}
                />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content - Tabular View */}
      <div className="bg-white rounded-b-lg border border-gray-200 shadow-sm">
        {activeCategory && (
          <div className="p-6">
            {/* Header with Generate All button */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-gray-900 font-satoshi">
                  {activeCategory.name} Notes
                </h3>
                <p className="text-gray-600 text-sm mt-1 font-satoshi">
                  {activeCategory.description}
                </p>
              </div>
              <button
                onClick={() => handleGenerateAll(activeCategory.id)}
                disabled={batchLoading || activeCategory.notes.length === 0}
                className="flex items-center gap-2 px-6 py-3 rounded-md transition-all font-medium shadow-sm text-white font-satoshi"
                style={{
                  backgroundColor: batchLoading || activeCategory.notes.length === 0 ? '#9ca3af' : PLAINFLOW_RED,
                  cursor: batchLoading || activeCategory.notes.length === 0 ? 'not-allowed' : 'pointer'
                }}
                onMouseEnter={(e) => {
                  if (!batchLoading && activeCategory.notes.length > 0) {
                    e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!batchLoading && activeCategory.notes.length > 0) {
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

            {/* Tabular View */}
            {activeCategory.notes.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-600 font-satoshi">No notes available for this category.</p>
              </div>
            ) : (
              <div className="overflow-x-auto border border-gray-300 rounded-lg">
                <table className="min-w-full divide-y divide-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider font-satoshi border-r border-gray-300">
                        Note
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider font-satoshi border-r border-gray-300">
                        Description
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider font-satoshi border-r border-gray-300">
                        Last Generated
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider font-satoshi border-r border-gray-300">
                        Status
                      </th>
                      <th scope="col" className="px-6 py-3 text-right text-sm font-bold text-gray-700 uppercase tracking-wider font-satoshi">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-300">
                    {activeCategory.notes.map((note) => {
                      const noteGeneratedFiles = groupedNotes[note.number] || [];
                      const latestGenerated = noteGeneratedFiles.length > 0 ? noteGeneratedFiles[0] : null;
                      const status = generationStatus[note.number] || 'idle';
                      
                      return (
                        <tr key={note.number} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900 font-satoshi border-r border-gray-300" style={{ fontSize: '0.9375rem' }}>
                            {note.number}
                          </td>
                          <td className="px-6 py-4 text-gray-900 font-satoshi border-r border-gray-300" style={{ fontSize: '0.9375rem' }}>
                            {note.title}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-gray-600 font-satoshi border-r border-gray-300" style={{ fontSize: '0.9375rem' }}>
                            {latestGenerated ? (
                              <div className="flex items-center gap-2">
                                <ClockIcon className="w-4 h-4 text-gray-400" />
                                {formatDate(latestGenerated.generated_at)}
                              </div>
                            ) : (
                              <span className="text-gray-400">Not generated</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap font-satoshi border-r border-gray-300" style={{ fontSize: '0.9375rem' }}>
                            {status === 'loading' ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-800 mr-1"></div>
                                Generating...
                              </span>
                            ) : status === 'success' ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                ✓ Success
                              </span>
                            ) : status === 'error' ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                ✗ Error
                              </span>
                            ) : latestGenerated ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                ✓ Generated
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                Not generated
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right font-medium font-satoshi" style={{ fontSize: '0.9375rem' }}>
                            <div className="flex items-center justify-end gap-2">
                              {latestGenerated && (
                                <>
                                  <button
                                    onClick={() => handleViewNote(latestGenerated)}
                                    disabled={loadingNoteContent}
                                    className="inline-flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                                    title="View Note"
                                  >
                                    {loadingNoteContent && viewingNote?.filename === latestGenerated.filename ? (
                                      <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-gray-700"></div>
                                    ) : (
                                      <EyeIcon className="w-4 h-4" />
                                    )}
                                    View
                                  </button>
                                  <button
                                    onClick={() => handleDownload(latestGenerated)}
                                    className="inline-flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors text-xs font-medium"
                                    title="Download as Excel"
                                  >
                                    <ArrowDownTrayIcon className="w-4 h-4" />
                                    Download
                                  </button>
                                </>
                              )}
                              <button
                                onClick={() => handleGenerateNote(note.number)}
                                disabled={status === 'loading'}
                                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-white font-medium transition-all text-xs"
                                style={{
                                  backgroundColor: status === 'loading' ? '#9ca3af' : PLAINFLOW_RED,
                                  cursor: status === 'loading' ? 'not-allowed' : 'pointer'
                                }}
                                onMouseEnter={(e) => {
                                  if (status !== 'loading') {
                                    e.currentTarget.style.backgroundColor = PLAINFLOW_RED_HOVER;
                                  }
                                }}
                                onMouseLeave={(e) => {
                                  if (status !== 'loading') {
                                    e.currentTarget.style.backgroundColor = PLAINFLOW_RED;
                                  }
                                }}
                              >
                                {status === 'loading' ? 'Generating...' : 'Generate Note'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Generated Note Display Modal */}
      {generatedNote && (
        <GeneratedNoteDisplay
          note={generatedNote}
          onClose={() => setGeneratedNote(null)}
        />
      )}

      {/* Batch Progress Modal */}
      {batchStatus && (
        <BatchProgress
          batchStatus={batchStatus}
          onClose={() => {
            setBatchStatus(null);
            setBatchId(null);
          }}
        />
      )}

      {/* Note Viewer Modal */}
      {viewingNote && (
        <TableNoteViewer
          noteNumber={viewingNote.note_number || ''}
          noteName={viewingNote.title || ''}
          content={viewingNoteContent}
          companyName={companyName}
          onClose={() => {
            setViewingNote(null);
            setViewingNoteContent('');
          }}
        />
      )}

      {/* Navigation */}
      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/step5')}
            className="btn-secondary"
          >
            ← Back to Step 5
          </button>
          <button
            onClick={() => navigate('/step7')}
            className="btn-primary"
          >
            Continue to Step 7 →
          </button>
        </div>
      </div>
    </div>
  );
};

export default Step6GenerateNotesTabular;
