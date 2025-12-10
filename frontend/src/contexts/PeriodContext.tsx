import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useEntity } from './EntityContext';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

interface PeriodContextType {
  // Current active period
  currentPeriod: string | null;           // e.g., "mar_2025"
  currentPeriodColumn: string | null;      // e.g., "Total Mar'25"
  
  // Available periods from backend
  availablePeriods: Record<string, string>; // { "mar_2025": "Total Mar'25", ... }
  periodDisplayNames: Record<string, string>; // { "mar_2025": "Mar-2025", ... }
  
  // Loading state
  loading: boolean;
  
  // Actions
  fetchPeriods: (entity?: string) => Promise<void>;
  setPeriod: (periodKey: string) => Promise<void>;
  addCustomPeriod: (periodKey: string, columnName: string) => Promise<void>;
  
  // Helper methods
  getPeriodDisplay: (periodKey: string) => string;
}

const PeriodContext = createContext<PeriodContextType | undefined>(undefined);

export const PeriodProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { selectedEntity } = useEntity();
  const [currentPeriod, setCurrentPeriod] = useState<string | null>(null);
  const [currentPeriodColumn, setCurrentPeriodColumn] = useState<string | null>(null);
  const [availablePeriods, setAvailablePeriods] = useState<Record<string, string>>({});
  const [periodDisplayNames, setPeriodDisplayNames] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  // Fetch periods when entity changes
  useEffect(() => {
    if (selectedEntity) {
      console.log('[PeriodContext] Entity changed, fetching periods for:', selectedEntity);
      // Reset current period when entity changes to avoid showing stale data
      setCurrentPeriod(null);
      setCurrentPeriodColumn(null);
      fetchPeriods(selectedEntity);
    }
  }, [selectedEntity]);

  // Fetch periods from backend
  const fetchPeriods = async (entity?: string) => {
    setLoading(true);
    try {
      const response = await apiService.getPeriods(entity);
      const data = response.data;
      
      // Get the available periods
      const periods = data.available_periods || {};
      const displayNames = data.period_display_names || data.available_periods || {};
      const periodKeys = Object.keys(periods);

      // Helper: find the latest period key (e.g., jun_2025 beats mar_2025)
      const monthOrder = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'];
      const parsePeriodKey = (key: string) => {
        const match = key.toLowerCase().match(/(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-_]?(\d{2,4})/);
        if (!match) return null;
        const monthIdx = monthOrder.indexOf(match[1]);
        const year = parseInt(match[2].length === 2 ? `20${match[2]}` : match[2], 10);
        if (monthIdx === -1 || Number.isNaN(year)) return null;
        return { year, month: monthIdx };
      };
      const latestPeriodKey = periodKeys.reduce<string | null>((latest, key) => {
        const parsed = parsePeriodKey(key);
        if (!parsed) return latest ?? key;
        if (!latest) return key;
        const latestParsed = parsePeriodKey(latest);
        if (!latestParsed) return key;
        if (parsed.year !== latestParsed.year) return parsed.year > latestParsed.year ? key : latest;
        return parsed.month > latestParsed.month ? key : latest;
      }, null);

      // Prefer per-entity remembered period, then backend-provided, then latest available
      const storedPeriodKey = entity ? localStorage.getItem(`period:${entity}`) : null;
      const isValidKey = (key?: string | null) => Boolean(key && periods[key]);
      let periodToUse: string | null = null;

      if (isValidKey(storedPeriodKey)) {
        periodToUse = storedPeriodKey as string;
      } else if (isValidKey(data.current_period)) {
        periodToUse = data.current_period;
      } else if (latestPeriodKey) {
        periodToUse = latestPeriodKey;
      }

      // Resolve the display column for the chosen period
      const columnToUse =
        (periodToUse ? periods[periodToUse] : null) || data.current_period_column || null;

      // Persist selection per entity so reloading/switching entities keeps the expected period
      if (entity && periodToUse) {
        localStorage.setItem(`period:${entity}`, periodToUse);
        // If backend value differs (or is missing), update backend to keep it in sync
        if (!isValidKey(data.current_period) || data.current_period !== periodToUse) {
          try {
            await apiService.setPeriod(periodToUse);
            console.log('[PeriodContext] ✅ Backend period updated for entity:', entity, periodToUse);
          } catch (error) {
            console.error('[PeriodContext] ❌ Failed to update backend period:', error);
          }
        }
      }
      
      setCurrentPeriod(periodToUse);
      setCurrentPeriodColumn(columnToUse);
      setAvailablePeriods(periods);
      setPeriodDisplayNames(displayNames);
      
      console.log('[PeriodContext] Loaded periods for entity:', entity, {
        periodToUse,
        columnToUse,
        periods,
        displayNames
      });
    } catch (error) {
      console.error('[PeriodContext] Error fetching periods:', error);
      toast.error('Failed to load period information');
    } finally {
      setLoading(false);
    }
  };

  // Set active period
  const setPeriod = async (periodKey: string) => {
    try {
      const response = await apiService.setPeriod(periodKey);
      const data = response.data;
      
      if (data.success) {
        setCurrentPeriod(data.period_key);
        setCurrentPeriodColumn(data.period_column);
        if (selectedEntity) {
          localStorage.setItem(`period:${selectedEntity}`, data.period_key);
        }
        toast.success(`Period set to ${data.period_column}`);
        console.log('[PeriodContext] Period updated:', data);
      }
    } catch (error: any) {
      console.error('[PeriodContext] Error setting period:', error);
      toast.error(error.response?.data?.detail || 'Failed to set period');
      throw error;
    }
  };

  // Add custom period
  const addCustomPeriod = async (periodKey: string, columnName: string) => {
    try {
      const response = await apiService.addCustomPeriod(periodKey, columnName);
      const data = response.data;
      
      if (data.success) {
        // Refresh periods list to include the new period
        await fetchPeriods();
        toast.success(`Custom period "${columnName}" added successfully`);
        console.log('[PeriodContext] Custom period added:', data);
      }
    } catch (error: any) {
      console.error('[PeriodContext] Error adding custom period:', error);
      toast.error(error.response?.data?.detail || 'Failed to add custom period');
      throw error;
    }
  };

  // Get display name for a period key
  const getPeriodDisplay = (periodKey: string): string => {
    return availablePeriods[periodKey] || periodKey;
  };

  return (
    <PeriodContext.Provider
      value={{
        currentPeriod,
        currentPeriodColumn,
        availablePeriods,
        periodDisplayNames,
        loading,
        fetchPeriods,
        setPeriod,
        addCustomPeriod,
        getPeriodDisplay,
      }}
    >
      {children}
    </PeriodContext.Provider>
  );
};

export const usePeriod = () => {
  const context = useContext(PeriodContext);
  if (context === undefined) {
    throw new Error('usePeriod must be used within a PeriodProvider');
  }
  return context;
};
