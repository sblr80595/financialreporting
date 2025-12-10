// FILE: src/pages/Step8GenerateCashFlow.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useEntity } from '../contexts/EntityContext';
import CashFlowGenerator from '../components/CashFlowGenerator';

const Step9GenerateCashFlow: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();

  return (
    <div className="space-y-6">
      {/* Info Card */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 font-satoshi">💵 Cash Flow Statement Generation</h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800 mb-2 font-satoshi">
            This step generates a comprehensive Cash Flow Statement by compiling all relevant notes from Step 6.
          </p>
          <p className="text-sm text-blue-800 font-satoshi">
            <strong>Cash Flow Components:</strong>
          </p>
          <ul className="text-sm text-blue-800 ml-4 mt-2 space-y-1 font-satoshi">
            <li>• <strong>Operating Activities:</strong> Cash from operations, working capital changes</li>
            <li>• <strong>Investing Activities:</strong> Capital expenditure, investments</li>
            <li>• <strong>Financing Activities:</strong> Loans, equity, dividends</li>
          </ul>
        </div>
      </div>

      {/* Cash Flow Generator Component */}
      <CashFlowGenerator 
        entity={getCompanyName()}
        defaultAsAtDate="31-03-2024"
        defaultForPeriod="Year ended"
      />

      {/* Navigation */}
      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/step8')}
            className="btn-secondary font-satoshi"
          >
            ← Back to Step 8
          </button>
          
          <button
            onClick={() => navigate('/feedback')}
            className="btn-primary font-satoshi"
          >
            Feedback →
          </button>
        </div>
      </div>
    </div>
  );
};

export default Step9GenerateCashFlow;