// src/pages/EntitySelectionPage.tsx

import React from 'react';
import { BuildingOffice2Icon, ChevronRightIcon, TableCellsIcon } from '@heroicons/react/24/outline';
import { Company } from '../types';

interface EntitySelectionPageProps {
  companies: Company[];
  onSelectEntity: (company: Company) => void;
}

const EntitySelectionPage: React.FC<EntitySelectionPageProps> = ({
  companies,
  onSelectEntity,
}) => {
  return (
    <div className="min-h-[calc(100vh-200px)] flex flex-col">
      {/* Hero Section */}
      <div className="text-center py-12 bg-gradient-to-b from-red-50 to-white">
        <div className="max-w-3xl mx-auto px-6">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Financial Note Generation
          </h1>
        </div>
      </div>

      {/* Entities Grid */}
      <div className="flex-1 max-w-7xl mx-auto px-6 py-12 w-full">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Available Entities
          </h2>
        </div>

        {companies.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <TableCellsIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 text-lg mb-2">No entities found</p>
            <p className="text-sm text-gray-500">
              Configure entity data to get started
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {companies.map((company) => (
              <button
                key={company.name}
                onClick={() => onSelectEntity(company)}
                className="bg-white rounded-xl border-2 border-gray-200 p-6 hover:shadow-xl hover:border-primary-600 transition-all text-left group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-primary-600 to-primary-700 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                    <BuildingOffice2Icon className="w-7 h-7 text-white" />
                  </div>
                  <ChevronRightIcon className="w-6 h-6 text-gray-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all" />
                </div>

                <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
                  {company.name}
                </h3>

                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <TableCellsIcon className="w-4 h-4" />
                    <span>{company.csv_file}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 flex items-center justify-center">
                      <span className="text-xs font-semibold">#</span>
                    </div>
                    <span>{company.notes_count} notes configured</span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100">
                  <span className="text-sm font-medium text-primary-600 group-hover:text-primary-700">
                    Generate Notes →
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default EntitySelectionPage;
