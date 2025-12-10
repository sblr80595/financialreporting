import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { EntityConfig, ENTITY_SHORT_TO_CODE, ENTITIES } from '../config/entities';

interface EntityContextType {
  selectedEntity: string;
  setSelectedEntity: (entity: string) => void;
  getCompanyName: (entityCode?: string) => string;
}

const EntityContext = createContext<EntityContextType | undefined>(undefined);

export const EntityProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Initialize from localStorage first to avoid a stale default during first render
  const [selectedEntity, setSelectedEntity] = useState<string>(() => {
    try {
      const saved = localStorage.getItem('selectedEntity');
      if (saved) {
        return EntityConfig.normalizeEntityCode(saved);
      }
    } catch (error) {
      console.warn('Unable to read saved entity from localStorage:', error);
    }
    return '';
  });

  // Persist to localStorage with migration for legacy entities
  useEffect(() => {
    const saved = localStorage.getItem('selectedEntity');
    if (saved) {
      // Normalize legacy entity codes (e.g., cpm_my -> cpm)
      const normalized = EntityConfig.normalizeEntityCode(saved);

      // If the saved value was a legacy code, update localStorage
      if (normalized !== saved) {
        console.log(`Migrating legacy entity code: ${saved} -> ${normalized}`);
        localStorage.setItem('selectedEntity', normalized);
      }

      if (normalized !== selectedEntity) {
        setSelectedEntity(normalized);
      }
    }
  }, [selectedEntity]);

  const handleSetEntity = (entity: string) => {
    setSelectedEntity(entity);
    localStorage.setItem('selectedEntity', entity);
  };

  // Convert entity short code to backend company code
  // If no entityCode provided, uses current selectedEntity
  const getCompanyName = (entityCode?: string): string => {
    const code = entityCode || selectedEntity;
    // Convert short code (e.g., 'CPM_MY') to backend code (e.g., 'cpm')
    return ENTITY_SHORT_TO_CODE[code] || EntityConfig.normalizeEntityCode(code);
  };

  return (
    <EntityContext.Provider value={{ 
      selectedEntity, 
      setSelectedEntity: handleSetEntity,
      getCompanyName 
    }}>
      {children}
    </EntityContext.Provider>
  );
};

export const useEntity = () => {
  const context = useContext(EntityContext);
  if (context === undefined) {
    throw new Error('useEntity must be used within an EntityProvider');
  }
  return context;
};
