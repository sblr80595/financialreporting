// FILE: src/pages/Step8GenerateBalanceSheet.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useEntity } from '../contexts/EntityContext';
import BalanceSheetGenerator from '../components/BalanceSheetGenerator';

const Step8GenerateBalanceSheet: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();

  return (
    <div className="space-y-6">
      {/* Info Card */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 font-satoshi">📊 Balance Sheet Generation</h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800 mb-2 font-satoshi">
            This step generates a comprehensive Balance Sheet by compiling all relevant notes from Step 6.
          </p>
          <p className="text-sm text-blue-800 font-satoshi">
            <strong>Balance Sheet Components:</strong>
          </p>
          <ul className="text-sm text-blue-800 ml-4 mt-2 space-y-1 font-satoshi">
            <li>• <strong>Assets:</strong> Non-current assets (Notes 3-5), Current assets (Notes 6-11)</li>
            <li>• <strong>Equity:</strong> Share capital (Note 15), Reserves (Notes 16-17)</li>
            <li>• <strong>Liabilities:</strong> Non-current liabilities (Notes 18-19), Current liabilities (Notes 20-23)</li>
          </ul>
        </div>
      </div>

      {/* Balance Sheet Generator Component */}
      <BalanceSheetGenerator 
        entity={getCompanyName()}
        defaultDate="31-03-2024"
      />

      {/* Navigation */}
      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/step7')}
            className="btn-secondary font-satoshi"
          >
            ← Back to Step 7
          </button>
          
          <button
            onClick={() => navigate('/step9')}
            className="btn-primary font-satoshi"
          >
            Continue to Step 9 →
          </button>
        </div>
      </div>
    </div>
  );
};

export default Step8GenerateBalanceSheet;