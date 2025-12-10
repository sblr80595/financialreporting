import React, { useState, useEffect } from 'react';
import { 
  CalendarIcon, 
  CheckCircleIcon, 
  PlusIcon, 
  XMarkIcon 
} from '@heroicons/react/24/outline';
import { usePeriod } from '../contexts/PeriodContext';
import toast from 'react-hot-toast';

interface PeriodSelectorProps {
  showInSidebar?: boolean;
  className?: string;
}

const PeriodSelector: React.FC<PeriodSelectorProps> = ({ 
  showInSidebar = true,
  className = ''
}) => {
  const { 
    currentPeriod,
    currentPeriodColumn,
    availablePeriods,
    periodDisplayNames,
    loading,
    setPeriod,
    addCustomPeriod,
    
  } = usePeriod();

  const [isChanging, setIsChanging] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState(currentPeriod || '');
  const [showAddCustom, setShowAddCustom] = useState(false);
  const [customPeriodKey, setCustomPeriodKey] = useState('');
  const [customColumnName, setCustomColumnName] = useState('');
  const [addingCustom, setAddingCustom] = useState(false);

  // Keep local selection in sync with context updates (important on first load without a hard refresh)
  useEffect(() => {
    setSelectedPeriod(currentPeriod || '');
  }, [currentPeriod]);

  const handleChangePeriod = async () => {
    if (!selectedPeriod || selectedPeriod === currentPeriod) {
      setIsChanging(false);
      return;
    }

    try {
      await setPeriod(selectedPeriod);
      setIsChanging(false);
    } catch (error) {
      console.error('Error changing period:', error);
    }
  };

  const handleAddCustomPeriod = async () => {
    if (!customPeriodKey.trim() || !customColumnName.trim()) {
      toast.error('Please fill in all fields');
      return;
    }

    setAddingCustom(true);
    try {
      await addCustomPeriod(customPeriodKey.trim(), customColumnName.trim());
      setShowAddCustom(false);
      setCustomPeriodKey('');
      setCustomColumnName('');
    } catch (error) {
      console.error('Error adding custom period:', error);
    } finally {
      setAddingCustom(false);
    }
  };

  const handleCancelChange = () => {
    setSelectedPeriod(currentPeriod || '');
    setIsChanging(false);
  };

  const handleCancelAddCustom = () => {
    setShowAddCustom(false);
    setCustomPeriodKey('');
    setCustomColumnName('');
  };

  // Compact view for sidebar
  if (showInSidebar) {
    return (
      <div className={`px-4 ${className}`}>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Period End
        </label>
        
        {loading ? (
          <div className="bg-white border border-gray-300 rounded-md p-3">
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
              <span className="text-xs text-gray-500">Loading...</span>
            </div>
          </div>
        ) : !isChanging ? (
          <div 
            onClick={() => setIsChanging(true)}
            className="cursor-pointer bg-white border border-gray-300 rounded-md p-3 hover:border-primary-500 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">
                  {currentPeriod && periodDisplayNames[currentPeriod] ? periodDisplayNames[currentPeriod] : (currentPeriodColumn || 'No period selected')}
                </div>
                <div className="text-xs text-gray-500">
                  {currentPeriodColumn || 'Click to select'}
                </div>
              </div>
              <CalendarIcon className="h-4 w-4 text-gray-400" />
            </div>
          </div>
        ) : showAddCustom ? (
          <div className="bg-white border-2 border-primary-500 rounded-md p-3 space-y-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-gray-700">Add Custom Period</span>
              <button
                onClick={handleCancelAddCustom}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            </div>

            <div>
              <input
                type="text"
                value={customPeriodKey}
                onChange={(e) => setCustomPeriodKey(e.target.value)}
                placeholder="Period Key (e.g., oct_2025)"
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <input
                type="text"
                value={customColumnName}
                onChange={(e) => setCustomColumnName(e.target.value)}
                placeholder="Column Name (e.g., Total Oct'25)"
                className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleAddCustomPeriod}
                disabled={addingCustom}
                className="flex-1 px-2 py-1.5 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {addingCustom ? 'Adding...' : 'Add'}
              </button>
              <button
                onClick={handleCancelAddCustom}
                className="flex-1 px-2 py-1.5 bg-gray-200 text-gray-700 text-xs font-medium rounded hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-white border-2 border-primary-500 rounded-md p-3 space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Select Period
              </label>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">-- Select Period --</option>
                {Object.entries(availablePeriods).map(([key, label]) => (
                  <option key={key} value={key}>
                    {periodDisplayNames[key] || label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setShowAddCustom(true)}
              className="w-full flex items-center justify-center gap-1 px-2 py-1.5 text-xs text-primary-600 border border-primary-300 rounded hover:bg-primary-50 transition-colors"
            >
              <PlusIcon className="h-3 w-3" />
              Add Custom Period
            </button>

            <div className="flex gap-2">
              <button
                onClick={handleChangePeriod}
                disabled={!selectedPeriod}
                className="flex-1 px-3 py-1.5 bg-primary-600 text-white text-xs font-medium rounded hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Apply
              </button>
              <button
                onClick={handleCancelChange}
                className="flex-1 px-3 py-1.5 bg-gray-200 text-gray-700 text-xs font-medium rounded hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Full card view for pages
  return (
    <div className={`card ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <CalendarIcon className="h-6 w-6 text-primary-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Period Information</h3>
        </div>
        {!isChanging && !loading && (
          <button
            onClick={() => setIsChanging(true)}
            className="btn-secondary text-sm"
          >
            Change Period
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-600">Loading period information...</span>
        </div>
      ) : !isChanging ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
                Current Period
              </div>
              <div className="text-lg font-semibold text-gray-900">
                {currentPeriodColumn || 'No period selected'}
              </div>
              <div className="text-sm text-gray-600 mt-1">
                Key: {currentPeriod}
              </div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-xs font-medium text-blue-700 uppercase tracking-wider mb-1">
                Available Periods
              </div>
              <div className="text-lg font-semibold text-blue-900">
                {Object.keys(availablePeriods).length} periods
              </div>
              <div className="text-sm text-blue-700 mt-1">
                Click "Change Period" to switch
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-xs text-yellow-800">
              <strong>Note:</strong> Changing the period will affect all note generations and financial statements.
            </p>
          </div>
        </div>
      ) : showAddCustom ? (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h4 className="font-semibold text-green-900 mb-2">Add Custom Period</h4>
            <p className="text-sm text-green-700 mb-4">
              Add a new period that's not in the default list.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Period Key
                </label>
                <input
                  type="text"
                  value={customPeriodKey}
                  onChange={(e) => setCustomPeriodKey(e.target.value)}
                  placeholder="e.g., oct_2025"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Format: lowercase with underscores (e.g., mar_2026, oct_2025)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Column Name
                </label>
                <input
                  type="text"
                  value={customColumnName}
                  onChange={(e) => setCustomColumnName(e.target.value)}
                  placeholder="e.g., Total Oct'25"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Display name as it appears in the Excel files
                </p>
              </div>
            </div>
          </div>

          <div className="flex gap-3 justify-end">
            <button
              onClick={handleCancelAddCustom}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleAddCustomPeriod}
              disabled={addingCustom}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              {addingCustom ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Adding...
                </>
              ) : (
                <>
                  <PlusIcon className="h-5 w-5" />
                  Add Custom Period
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Period
            </label>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">-- Select Period --</option>
              {Object.entries(availablePeriods).map(([key, label]) => (
                <option key={key} value={key}>
                  {periodDisplayNames[key] || label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setShowAddCustom(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-primary-600 border-2 border-dashed border-primary-300 rounded-lg hover:bg-primary-50 transition-colors"
          >
            <PlusIcon className="h-5 w-5" />
            Add Custom Period
          </button>

          <div className="flex gap-3 justify-end">
            <button
              onClick={handleCancelChange}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleChangePeriod}
              disabled={!selectedPeriod}
              className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircleIcon className="h-5 w-5" />
              Apply Period
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PeriodSelector;
