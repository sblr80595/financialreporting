// src/pages/ViewCashFlowPage.tsx

import React from 'react';
import { useEntity } from '../contexts/EntityContext';
import FinancialStatementViewer from '../components/statements/FinancialStatementViewer';

const ViewCashFlowPage: React.FC = () => {
  const { selectedEntity } = useEntity();

  return (
    <FinancialStatementViewer
      companyName={selectedEntity}
      statementType="CashFlow"
    />
  );
};

export default ViewCashFlowPage;
