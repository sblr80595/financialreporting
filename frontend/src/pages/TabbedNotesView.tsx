// src/pages/TabbedNotesView.tsx

import React, { useState } from 'react';
import { Company, NoteCategory, GenerationStatusMap } from '../types';
import CompanyDetailsPage from './CompanyDetailsPage';

interface TabbedNotesViewProps {
  company: Company;
  categories: NoteCategory[];
  generationStatus: GenerationStatusMap;
  onGenerateNote: (noteNumber: string) => void;
  onGenerateAll: (categoryId: string) => void; // Changed to accept categoryId
  onBack: () => void;
  batchLoading?: boolean;
}

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';

const TabbedNotesView: React.FC<TabbedNotesViewProps> = ({
  company,
  categories,
  generationStatus,
  onGenerateNote,
  onGenerateAll,
  onBack,
  batchLoading = false,
}) => {
  const [activeTab, setActiveTab] = useState<string>(categories[0]?.id || '');

  const activeCategory = categories.find(cat => cat.id === activeTab);

  return (
    <div className="mx-auto px-6 py-8">
      {/* Tab Navigation */}
      <div className="bg-white rounded-t-lg border border-b-0 border-gray-200 shadow-sm">
        <div className="flex overflow-x-auto">
          {categories.map((category) => (
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

      {/* Tab Content */}
      <div className="bg-white rounded-b-lg border border-gray-200 shadow-sm">
        {activeCategory && (
          <CompanyDetailsPage
            company={company}
            category={activeCategory}
            generationStatus={generationStatus}
            onGenerateNote={onGenerateNote}
            onGenerateAll={() => onGenerateAll(activeCategory.id)} // Pass the active category ID
            onBack={onBack}
            batchLoading={batchLoading}
            hideHeader={true} // Add this prop to hide the duplicate header in CompanyDetailsPage
          />
        )}
      </div>
    </div>
  );
};

export default TabbedNotesView;
