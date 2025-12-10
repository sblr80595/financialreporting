// src/pages/ViewPLStatementPage.tsx

import React from 'react';
import { useEntity } from '../contexts/EntityContext';
import FinancialStatementViewer from '../components/statements/FinancialStatementViewer';

const ViewPLStatementPage: React.FC = () => {
  const { selectedEntity } = useEntity();

  return (
    <FinancialStatementViewer
      companyName={selectedEntity}
      statementType="PnL"
    />
  );
};

export default ViewPLStatementPage;
