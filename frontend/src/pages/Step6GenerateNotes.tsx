import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';
import { NoteCategory, GenerationStatusMap, GenerationResponse, BatchStatus } from '../types';
import { useEntity } from '../contexts/EntityContext';

// Import new components
import TabbedNotesView from './TabbedNotesView';
import GeneratedNoteDisplay from '../components/GeneratedNoteDisplay';
import BatchProgress from '../components/BatchProgress';

const Step6GenerateNotes: React.FC = () => {
  const navigate = useNavigate();
  const { selectedEntity, getCompanyName } = useEntity();
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

  const loadCategories = useCallback(async (attempt = 0) => {
    try {
      setLoading(true);
      const categories = await apiService.getCompanyCategories(companyName);
      setAvailableCategories(categories);
      setRetryCount(0); // Reset retry count on success
      setLoading(false); // Success - stop loading
    } catch (err: any) {
      console.error('Error loading categories:', err);
      
      // Retry logic with exponential backoff
      if (attempt < 3) {
        const delay = Math.min(1000 * Math.pow(2, attempt), 5000); // Max 5 seconds
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
  }, [companyName]);

  // Load categories when entity changes
  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  // Poll batch status with improved error handling
  useEffect(() => {
    let interval: NodeJS.Timeout;
    let consecutiveErrors = 0;
    const maxConsecutiveErrors = 5;
    
    if (batchId && (batchStatus?.status === 'running' || batchStatus?.status === 'pending')) {
      interval = setInterval(async () => {
        try {
          const status = await apiService.getBatchStatus(batchId);
          setBatchStatus(status);
          consecutiveErrors = 0; // Reset error count on success
          
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(interval);
            
            // Reload categories to show newly generated notes
            loadCategories();
            
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
          
          // Only show error and stop polling if we have too many consecutive errors
          if (consecutiveErrors >= maxConsecutiveErrors) {
            clearInterval(interval);
            toast.error('Lost connection to batch generation. Please check the backend logs.');
          }
        }
      }, 3000); // Poll every 3 seconds (increased from 2)
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [batchId, batchStatus?.status, loadCategories]);

  // Generate a single note
  const handleGenerateNote = async (noteNumber: string) => {
    setGenerationStatus(prev => ({ ...prev, [noteNumber]: 'loading' }));
    
    try {
      const result = await apiService.generateNote(companyName, noteNumber);
      setGenerationStatus(prev => ({ ...prev, [noteNumber]: 'success' }));
      setGeneratedNote(result);
      toast.success(`Note ${noteNumber} generated successfully!`);
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
      
      // Wait a bit for the backend to initialize the batch
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

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        {/* <div className="bg-gradient-to-r from-orange-600 to-orange-800 rounded-lg shadow-soft">
          <div className="px-6 py-8">
            <div className="flex items-center">
              <DocumentTextIcon className="h-12 w-12 text-white" />
              <div className="ml-4">
                <h1 className="text-3xl font-bold text-white">
                  Step 6: Generate Notes
                </h1>
                <p className="mt-2 text-orange-100">
                  Part 2: Financial Statement Generation
                </p>
              </div>
            </div>
          </div>
        </div> */}
        <div className="card text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          {retryCount > 0 && (
            <p className="text-sm text-gray-500 mt-2">Retry attempt {retryCount}/3</p>
          )}
        </div>
      </div>
    );
  }

  // Create a company object for compatibility with existing components
  const company = {
    name: companyName,
    csv_file: `${selectedEntity}.csv`,
    notes_count: availableCategories.reduce((sum, cat) => sum + cat.notes.length, 0),
    notes: availableCategories.flatMap(cat => cat.notes)
  };

  // Render content based on selection state
  const renderContent = () => {
    return (
      <TabbedNotesView
        company={company}
        categories={availableCategories}
        generationStatus={generationStatus}
        onGenerateNote={handleGenerateNote}
        onGenerateAll={handleGenerateAll}
        onBack={() => navigate('/step5')}
        batchLoading={batchLoading}
      />
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      {/* <div className="bg-gradient-to-r from-orange-600 to-orange-800 rounded-lg shadow-soft">
        <div className="px-6 py-8">
          <div className="flex items-center">
            <DocumentTextIcon className="h-12 w-12 text-white" />
            <div className="ml-4">
              <h1 className="text-3xl font-bold text-white">
                Step 6: Generate Notes
              </h1>
              <p className="mt-2 text-orange-100">
                Part 2: Financial Statement Generation
              </p>
            </div>
          </div>
        </div>
      </div> */}

      {/* Content */}
      {renderContent()}

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

export default Step6GenerateNotes;
