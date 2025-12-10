// src/pages/ViewBalanceSheetPage.tsx

import React from 'react';
import { useEntity } from '../contexts/EntityContext';
import FinancialStatementViewer from '../components/statements/FinancialStatementViewer';

const ViewBalanceSheetPage: React.FC = () => {
  const { selectedEntity } = useEntity();

  return (
    <FinancialStatementViewer
      companyName={selectedEntity}
      statementType="BalanceSheet"
    />
  );
};

export default ViewBalanceSheetPage;
