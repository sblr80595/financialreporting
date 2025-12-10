// src/pages/FinAnalyzerCategorySelection.tsx

import React from 'react';
import { ArrowLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface FinAnalyzerCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
}

interface FinAnalyzerCategorySelectionProps {
  companyName: string;
  categories: FinAnalyzerCategory[];
  onSelectCategory: (category: FinAnalyzerCategory) => void;
  onBack: () => void;
}

const PLAINFLOW_RED = 'rgb(139, 0, 16)';
const PLAINFLOW_RED_HOVER = 'rgb(110, 0, 13)';

const FinAnalyzerCategorySelection: React.FC<FinAnalyzerCategorySelectionProps> = ({
  companyName,
  categories,
  onSelectCategory,
  onBack,
}) => {
  const getCategoryGradient = () => {
    return `linear-gradient(to right, ${PLAINFLOW_RED}, ${PLAINFLOW_RED_HOVER})`;
  };

  return (
    <div className="mx-auto px-6 py-8">
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6 shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors font-satoshi"
          >
            <ArrowLeftIcon className="w-5 h-5" />
            <span className="font-medium">Back</span>
          </button>
          <div className="border-l border-gray-300 pl-4">
            <h2 className="text-2xl font-bold text-gray-900 font-satoshi">{companyName}</h2>
            <p className="text-gray-600 text-sm mt-1 font-satoshi">
              Select a FinAnalyzer report to generate
            </p>
          </div>
        </div>
      </div>

      {/* Categories Grid */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gray-900 font-satoshi">FinAnalyzer Reports</h3>
        <p className="text-gray-600 text-sm mt-1 font-satoshi">
          Choose a report type to generate
        </p>
      </div>

      {categories.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <p className="text-gray-600 font-satoshi">No reports available for this company.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => onSelectCategory(category)}
              className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-xl transition-all hover:border-gray-300 text-left group relative overflow-hidden"
            >
              {/* Gradient Background */}
              <div 
                className="absolute top-0 left-0 right-0 h-2"
                style={{ background: getCategoryGradient() }}
              />
              
              {/* Content */}
              <div className="flex items-start justify-between mb-4 mt-2">
                <div className="text-4xl">{category.icon}</div>
                <ChevronRightIcon className="w-5 h-5 text-gray-400 group-hover:text-gray-900 group-hover:translate-x-1 transition-all" />
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 mb-2 font-satoshi">
                {category.name}
              </h3>
              
              <p className="text-sm text-gray-600 mb-4 font-satoshi">
                {category.description}
              </p>
              
              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <span className="text-sm font-medium text-gray-700 font-satoshi">
                  Ready to Generate
                </span>
                <div 
                  className="px-4 py-1.5 rounded-full text-xs font-semibold text-white"
                  style={{ background: getCategoryGradient() }}
                >
                  Generate
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default FinAnalyzerCategorySelection;
