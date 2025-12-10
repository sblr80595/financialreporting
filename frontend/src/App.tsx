import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { EntityProvider } from './contexts/EntityContext';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import Header from './components/Header';
import UnifiedDashboard from './pages/UnifiedDashboard';
import Step1UploadTB from './pages/Step1UploadTB';
import Step2UploadAdjustments from './pages/Step2UploadAdjustments';
import Step3ApplyAdjustments from './pages/Step3ApplyAdjustments';
import Step4MapCategories from './pages/Step4MapCategories';
import Step5ValidateRules from './pages/Step5ValidateRules';
import Step5ValidateRulesUpdated from './pages/Step5ValidateRulesUpdated';
import Step4CategoryMapping from './pages/Step4CategoryMapping';
import Step6GenerateNotes from './pages/Step6GenerateNotes';
import Step6GenerateNotesTabular from './pages/Step6GenerateNotesTabular';
import Step7GeneratePandL from './pages/Step7GeneratePandL';
import Step8GenerateBalanceSheet from './pages/Step8GenerateBalanceSheet';
import Step9GenerateCashFlow from './pages/Step9GenerateCashFlow';
import FinAnalyzerReportsPage from './pages/FinAnalyzerReportsPage';
import AdjustmentsPreview from './pages/AdjustmentsPreview';
import ViewStatementsPage from './pages/ViewStatementsPage';
import ViewPLStatementPage from './pages/ViewPLStatementPage';
import ViewBalanceSheetPage from './pages/ViewBalanceSheetPage';
import ViewCashFlowPage from './pages/ViewCashFlowPage';
import { PeriodProvider } from './contexts/PeriodContext';
import Feedback from './pages/Feedback';
import { CurrencySelectionProvider } from './contexts/CurrencySelectionContext';
import { useEntity } from './contexts/EntityContext';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: false,
      staleTime: 5 * 60 * 1000, // 5 minutes default
    },
  },
});

const CurrencyProviderWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { selectedEntity } = useEntity();
  return (
    <CurrencySelectionProvider entity={selectedEntity || ''}>
      {children}
    </CurrencySelectionProvider>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <EntityProvider>
          <PeriodProvider>
            <Router>
              <CurrencyProviderWrapper>
                <div className="min-h-screen bg-gray-50">
                  <Header title="Financial Close & Reporting Platform" />
                  <Layout>
                    <Routes>
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                      <Route path="/dashboard" element={<UnifiedDashboard />} />
                      <Route path="/step1" element={<Step1UploadTB />} />
                      <Route path="/step2" element={<Step2UploadAdjustments />} />
                      <Route path="/step3" element={<Step3ApplyAdjustments />} />
                      <Route path="/step4" element={<Step4MapCategories />} />
                      <Route path="/step4-category-mapping" element={<Step4CategoryMapping />} />
                      <Route path="/step5" element={<Step5ValidateRules />} />
                      <Route path="/step5-updated" element={<Step5ValidateRulesUpdated />} />
                      <Route path="/step6" element={<Step6GenerateNotes />} />
                      <Route path="/step6-tabular" element={<Step6GenerateNotesTabular />} />
                      <Route path="/step7" element={<Step7GeneratePandL />} />
                      <Route path="/step8" element={<Step8GenerateBalanceSheet />} />
                      <Route path="/step9" element={<Step9GenerateCashFlow />} />
                      <Route path="/finalyzer-reports" element={<FinAnalyzerReportsPage />} />
                      <Route path="/adjustments-preview" element={<AdjustmentsPreview />} />
                      <Route path="/view-statements" element={<ViewStatementsPage />} />
                      <Route path="/view-statements/pnl" element={<ViewPLStatementPage />} />
                      <Route path="/view-statements/balancesheet" element={<ViewBalanceSheetPage />} />
                      <Route path="/view-statements/cashflow" element={<ViewCashFlowPage />} />
                      <Route path="/feedback" element={<Feedback />} />
                    </Routes>
                  </Layout>
                  <Toaster
                    position="top-right"
                    toastOptions={{
                      duration: 4000,
                      style: {
                        background: '#fff',
                        color: '#333',
                      },
                    }}
                  />
                </div>
              </CurrencyProviderWrapper>
            </Router>
          </PeriodProvider>
        </EntityProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;