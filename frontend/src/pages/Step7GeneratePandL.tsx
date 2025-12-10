// src/pages/Step7GeneratePandL.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useEntity } from '../contexts/EntityContext';
import PLStatementGenerator from '../components/PLStatementGenerator';

const Step7GeneratePandL: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();

  return (
    <div className="space-y-6">
      {/* Info Card */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 font-satoshi">📊 P&L Statement Generation</h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800 mb-2 font-satoshi">
            This step generates a comprehensive Profit & Loss Statement by compiling all relevant Notes.
          </p>
          <p className="text-sm text-blue-800 font-satoshi">
            <strong>Required Notes:</strong>
          </p>
          <ul className="text-sm text-blue-800 ml-4 mt-2 space-y-1 font-satoshi">
            <li>• <strong>Income Notes:</strong> Notes 24, 25 (Revenue from operations, Other income)</li>
            <li>• <strong>Expense Notes:</strong> Notes 26-31 (Purchases, Inventory changes, Employee benefits, Finance costs, Depreciation, Other expenses)</li>
            <li>• <strong>Tax Notes:</strong> Note 32 (Tax expense)</li>
          </ul>
        </div>
      </div>

      {/* P&L Statement Generator Component */}
      <PLStatementGenerator 
        companyName={getCompanyName()}
        categoryId="profit-loss"
      />

      {/* Navigation */}
      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/step6')}
            className="btn-secondary font-satoshi"
          >
            ← Back to Step 6
          </button>
          
          <button
            onClick={() => navigate('/step8')}
            className="btn-primary font-satoshi"
          >
            Continue to Step 8 →
          </button>
        </div>
      </div>
    </div>
  );
};

export default Step7GeneratePandL;