import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from 'react-query';
import {
  CheckCircleIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
  XMarkIcon,
  AdjustmentsHorizontalIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';
import { useEntity } from '../contexts/EntityContext';
import FileManager from '../components/FileManager';

// Interface for rule toggle state
interface RuleToggleState {
  [key: string]: boolean;
}

const Step5ValidateRules: React.FC = () => {
  const navigate = useNavigate();
  const { getCompanyName } = useEntity();
  const [validationResult, setValidationResult] = useState<any>(null);
  const [showIssuesModal, setShowIssuesModal] = useState(false);

  // State for rule toggles - initialized from config
  const [ruleToggles, setRuleToggles] = useState<RuleToggleState>({});
  const [hasCustomOverrides, setHasCustomOverrides] = useState(false);

  // Fetch entity-specific validation rules configuration
  const { data: rulesConfig, isLoading: isLoadingRules } = useQuery(
    ['validation-rules', getCompanyName()],
    () => apiService.getValidationRulesConfig(getCompanyName()),
    {
      enabled: true,
      refetchOnMount: 'always',
      onSuccess: (response) => {
        console.log('[Step 5] Validation rules config:', response.data);
        // Initialize toggle state from config defaults
        if (response.data?.rules) {
          const initialToggles: RuleToggleState = {};
          response.data.rules.forEach((rule: any) => {
            initialToggles[`rule_${rule.rule_number}`] = rule.enabled;
          });
          setRuleToggles(initialToggles);
          setHasCustomOverrides(false);
        }
      },
      onError: (error) => {
        console.error('[Step 5] Error fetching validation rules:', error);
      }
    }
  );

  // Handle toggle change
  const handleToggleRule = (ruleKey: string) => {
    setRuleToggles(prev => {
      const newToggles = { ...prev, [ruleKey]: !prev[ruleKey] };
      // Check if any toggle differs from default
      const defaultRules = rulesConfig?.data?.rules || [];
      const hasOverrides = defaultRules.some((rule: any) =>
        newToggles[`rule_${rule.rule_number}`] !== rule.enabled
      );
      setHasCustomOverrides(hasOverrides);
      return newToggles;
    });
  };

  // Reset to default configuration
  const handleResetToDefaults = () => {
    if (rulesConfig?.data?.rules) {
      const initialToggles: RuleToggleState = {};
      rulesConfig.data.rules.forEach((rule: any) => {
        initialToggles[`rule_${rule.rule_number}`] = rule.enabled;
      });
      setRuleToggles(initialToggles);
      setHasCustomOverrides(false);
      toast.success('Reset to default configuration');
    }
  };

  // Get count of enabled rules
  const enabledRulesCount = Object.values(ruleToggles).filter(Boolean).length;
  const totalRulesCount = Object.keys(ruleToggles).length;

  // Check for existing validation report - AUTO FETCH on mount
  const { data: filesData, refetch: refetchFiles, isLoading: isLoadingFiles } = useQuery(
    ['entity-files-step5', getCompanyName()],
    () => apiService.listEntityFiles(getCompanyName()),
    {
      enabled: true, // Auto-fetch on mount
      refetchOnMount: 'always', // Always refetch when component mounts
      refetchOnWindowFocus: false,
      staleTime: 0, // Always consider data stale to ensure refetch
      cacheTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
      onSuccess: (response) => {
        console.log('[Step 5] Full API response:', response);
        console.log('[Step 5] Response data:', response.data);
      },
      onError: (error) => {
        console.error('[Step 5] Error fetching files:', error);
      }
    }
  );

  // Helper function to extract filename from string or object
  const getFilename = (file: string | { filename: string }): string => {
    return typeof file === 'string' ? file : file.filename;
  };

  // Get existing files from query data
  const adjustedFiles = filesData?.data?.adjusted_trialbalance || [];
  const existingValidationFiles = adjustedFiles.filter((f: string | { filename: string }) => {
    const filename = getFilename(f).toLowerCase();
    return filename.includes('validation') && 
      filename.includes('report') &&
      !filename.includes('insights');
  });

  const validateMutation = useMutation(
    ({ entity, ruleOverrides }: { entity: string; ruleOverrides?: RuleToggleState }) =>
      apiService.validate6RulesWithOverrides(entity, ruleOverrides),
    {
      onSuccess: (response) => {
        setValidationResult(response.data);
        toast.success('Validation completed successfully!');
        refetchFiles(); // Refresh file list
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Validation failed');
      },
    }
  );

  const generateInsightsMutation = useMutation(
    (entity: string) => apiService.generateValidationInsights(entity),
    {
      onSuccess: (response) => {
        console.log('[Step 5] Insights generated:', response.data);
        toast.success('AI Insights generated successfully!');
        refetchFiles(); // Refresh file list to show new insights report
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to generate insights');
      },
    }
  );

  const handleValidate = () => {
    // Pass rule overrides if user has made custom changes
    validateMutation.mutate({
      entity: getCompanyName(),
      ruleOverrides: hasCustomOverrides ? ruleToggles : undefined
    });
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleGenerateInsights = () => {
    if (!validationResult && existingValidationFiles.length === 0) {
      toast.error('Please run validation first before generating insights');
      return;
    }
    generateInsightsMutation.mutate(getCompanyName());
  };

  const handleDownloadValidationReport = async () => {
    try {
      // Try to find the validation report file
      const reportFileObj = existingValidationFiles.length > 0 
        ? existingValidationFiles[0] 
        : 'trialbalance_7rule_validation_report.xlsx';
      
      const reportFile = typeof reportFileObj === 'string' 
        ? reportFileObj 
        : reportFileObj.filename;
      
      console.log('[Step 5] Downloading validation report:', reportFile);
      
      const response = await apiService.downloadEntityFile(
        getCompanyName(), 
        'adjusted_trialbalance', 
        reportFile
      );
      
      // Create blob and download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', reportFile);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Downloaded ${reportFile}`);
    } catch (error: any) {
      console.error('[Step 5] Download error:', error);
      toast.error(error.response?.data?.detail || 'Failed to download validation report');
    }
  };

  const handleIgnoreAndContinue = () => {
    toast('Validation issues ignored - proceeding to next step', { icon: 'ℹ️' });
    navigate('/step6');
  };

  const handleRejectAndReview = () => {
    setShowIssuesModal(true);
  };

  // Get validation rules from API response or use defaults
  const validationRules = rulesConfig?.data?.rules || [
    {
      rule_number: 1,
      rule_name: 'Total Debits Equal Total Credits',
      description: 'The sum of all debit amounts must equal the sum of all credit amounts',
      enabled: true,
      category: 'Balance Validation',
      severity: 'critical',
      notes: 'This rule ensures the fundamental accounting equation is maintained'
    },
    {
      rule_number: 2,
      rule_name: 'Balance Calculation Accuracy',
      description: 'Each row\'s Balance must equal (Debit - Credit)',
      enabled: true,
      category: 'Data Integrity',
      severity: 'critical',
      notes: 'Ensures individual GL account balances are correctly calculated'
    },
    {
      rule_number: 3,
      rule_name: 'No Duplicate Accounts',
      description: 'Each G/L Acct/BP Code must be unique',
      enabled: true,
      category: 'Data Integrity',
      severity: 'critical',
      notes: 'Prevents duplicate GL codes which can cause reporting errors'
    },
    {
      rule_number: 4,
      rule_name: 'No Missing or Invalid Data',
      description: 'All rows must have valid codes, names, and numeric values',
      enabled: true,
      category: 'Data Integrity',
      severity: 'critical',
      notes: 'Ensures completeness of trial balance data'
    },
    {
      rule_number: 5,
      rule_name: 'Logical Balance Signs by Account Type',
      description: 'Assets (1xxxxx): Positive | Liabilities (2xxxxx): Negative | Revenue (3xxxxx): Negative | Expenses (4xxxxx): Positive | Equity (5xxxxx): Negative',
      enabled: true,
      category: 'Business Logic',
      severity: 'warning',
      notes: 'Validates account balances have expected signs based on account type'
    },
    {
      rule_number: 6,
      rule_name: 'Accounting Equation Balance',
      description: 'Assets = -(Liabilities + Equity + Revenue + Expenses)',
      enabled: true,
      category: 'Balance Validation',
      severity: 'critical',
      notes: 'Ensures the fundamental accounting equation balances'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Loading State */}
      {isLoadingFiles && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <p className="text-blue-700">Checking for existing validation reports...</p>
          </div>
        </div>
      )}

      {/* Existing Validation Results - Simple & Clean */}
      {!isLoadingFiles && existingValidationFiles.length > 0 && !validationResult && (
        <div className="card bg-green-50 border-2 border-green-300">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <div>
                <h3 className="text-lg font-semibold text-green-900">
                  Validation Already Completed
                </h3>
                <p className="text-sm text-green-700">
                  {existingValidationFiles.length} report(s) available • Ready to proceed to Step 6
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                toast.success('Proceeding with existing validation');
                navigate('/step6');
              }}
              className="btn-primary bg-green-600 hover:bg-green-700 flex items-center space-x-2"
            >
              <span>Continue to Step 6</span>
            </button>
          </div>
          
          {/* File List with Download */}
          <div className="bg-white rounded border border-green-200 p-4">
            <FileManager 
              files={existingValidationFiles}
              folderType="adjusted_trialbalance"
              entity={getCompanyName()}
              onDelete={refetchFiles}
            />
          </div>

          {/* Generate AI Insights for Existing Validation - COMMENTED OUT */}
          {/* <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <LightBulbIcon className="h-5 w-5 text-purple-600 mt-1" />
                <div>
                  <h4 className="text-sm font-semibold text-purple-900">Need help understanding failures?</h4>
                  <p className="text-xs text-purple-700">Generate AI-powered insights and recommendations</p>
                </div>
              </div>
              <button
                onClick={handleGenerateInsights}
                disabled={generateInsightsMutation.isLoading}
                className="btn-primary bg-purple-600 hover:bg-purple-700 text-sm flex items-center space-x-2"
              >
                {generateInsightsMutation.isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <LightBulbIcon className="h-4 w-4" />
                    <span>Generate Insights</span>
                  </>
                )}
              </button>
            </div>
          </div> */}

          {/* Show Insights Report if Available - COMMENTED OUT */}
          {/* {insightsReport && (
            <div className="mt-2 p-3 bg-green-100 border border-green-300 rounded flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
                <span className="text-sm text-green-900 font-medium">AI Insights Report Ready</span>
              </div>
              <button
                onClick={async () => {
                  try {
                    const insightsFilename = getFilename(insightsReport);
                    const response = await apiService.downloadEntityFile(
                      getCompanyName(),
                      'adjusted_trialbalance',
                      insightsFilename
                    );
                    const url = window.URL.createObjectURL(new Blob([response.data]));
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', insightsFilename);
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    window.URL.revokeObjectURL(url);
                    toast.success('Downloaded AI Insights Report');
                  } catch (error) {
                    toast.error('Failed to download insights report');
                  }
                }}
                className="btn-primary bg-green-600 hover:bg-green-700 text-sm flex items-center space-x-1"
              >
                <ArrowDownTrayIcon className="h-4 w-4" />
                <span>Download</span>
              </button>
            </div>
          )} */}
        </div>
      )}

      {/* Execute Validation - Simple Execution */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {existingValidationFiles.length > 0 ? 'Re-run 6 Rules Validation' : 'Execute 6 Rules Validation'}
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Validates the Final Adjusted Trial Balance against 6 fundamental accounting rules
        </p>
        
        <button
          onClick={handleValidate}
          disabled={validateMutation.isLoading}
          className={`btn-primary ${
            existingValidationFiles.length > 0
              ? 'bg-yellow-500 hover:bg-yellow-600'
              : ''
          }`}
        >
          {validateMutation.isLoading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Validating...
            </>
          ) : (
            <>
              <CheckCircleIcon className="h-5 w-5 mr-2" />
              {existingValidationFiles.length > 0 ? '🔄 Re-run Validation' : '✅ Execute Validation'}
            </>
          )}
        </button>
      </div>

      {/* Validation Rules Information - Dynamic per Entity with Toggle Controls */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <AdjustmentsHorizontalIcon className="h-6 w-6 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Validation Rules Configuration</h2>
          </div>
          <div className="flex items-center space-x-4">
            {rulesConfig?.data && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">{rulesConfig.data.entity_name}</span>
                {' • '}
                <span className={`font-semibold ${enabledRulesCount > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {enabledRulesCount}/{totalRulesCount} enabled
                </span>
              </div>
            )}
            {hasCustomOverrides && (
              <button
                onClick={handleResetToDefaults}
                className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
              >
                <ArrowPathIcon className="h-4 w-4" />
                <span>Reset to Default</span>
              </button>
            )}
          </div>
        </div>

        {/* Custom Override Warning Banner */}
        {hasCustomOverrides && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-300 rounded-lg flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-yellow-600 text-lg">⚠️</span>
              <span className="text-sm text-yellow-800">
                <strong>Custom configuration active.</strong> You have modified the default rule settings for this session.
              </span>
            </div>
            <span className="text-xs text-yellow-600 bg-yellow-100 px-2 py-1 rounded">
              Changes are temporary
            </span>
          </div>
        )}

        {isLoadingRules ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading validation rules...</span>
          </div>
        ) : (
          <>
            {/* Rules Grid with Toggle Buttons */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              {validationRules.map((rule: any) => {
                const ruleKey = `rule_${rule.rule_number}`;
                const isEnabled = ruleToggles[ruleKey] ?? rule.enabled;
                const isDefaultEnabled = rule.enabled;

                return (
                  <div
                    key={rule.rule_number}
                    className={`p-4 border-2 rounded-lg transition-all duration-200 ${
                      isEnabled
                        ? 'border-green-300 bg-green-50'
                        : 'border-gray-200 bg-gray-50 opacity-60'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start flex-1">
                        <span
                          className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-semibold text-sm mr-3 ${
                            isEnabled
                              ? 'bg-green-600 text-white'
                              : 'bg-gray-400 text-white'
                          }`}
                        >
                          {rule.rule_number}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h3 className={`text-sm font-semibold ${isEnabled ? 'text-gray-900' : 'text-gray-500'}`}>
                              {rule.rule_name}
                            </h3>
                            {!isDefaultEnabled && (
                              <span className="text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded">
                                Default: OFF
                              </span>
                            )}
                          </div>
                          <p className={`text-xs mt-1 ${isEnabled ? 'text-gray-600' : 'text-gray-400'}`}>
                            {rule.description}
                          </p>
                          <div className="flex items-center space-x-2 mt-2">
                            {rule.category && (
                              <span className={`text-xs px-2 py-0.5 rounded ${
                                isEnabled ? 'bg-blue-100 text-blue-700' : 'bg-gray-200 text-gray-500'
                              }`}>
                                {rule.category}
                              </span>
                            )}
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              rule.severity === 'critical'
                                ? isEnabled ? 'bg-red-100 text-red-700' : 'bg-gray-200 text-gray-500'
                                : isEnabled ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-200 text-gray-500'
                            }`}>
                              {rule.severity}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Toggle Switch */}
                      <div className="ml-4">
                        <button
                          onClick={() => handleToggleRule(ruleKey)}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                            isEnabled ? 'bg-green-600' : 'bg-gray-300'
                          }`}
                          role="switch"
                          aria-checked={isEnabled}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                              isEnabled ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                    </div>

                    {/* Show notes if available */}
                    {rule.notes && (
                      <p className={`text-xs mt-2 italic ${isEnabled ? 'text-green-700' : 'text-gray-400'}`}>
                        💡 {rule.notes}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Quick Actions */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => {
                    const allEnabled: RuleToggleState = {};
                    validationRules.forEach((rule: any) => {
                      allEnabled[`rule_${rule.rule_number}`] = true;
                    });
                    setRuleToggles(allEnabled);
                    setHasCustomOverrides(true);
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  Enable All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={() => {
                    const allDisabled: RuleToggleState = {};
                    validationRules.forEach((rule: any) => {
                      allDisabled[`rule_${rule.rule_number}`] = false;
                    });
                    setRuleToggles(allDisabled);
                    setHasCustomOverrides(true);
                  }}
                  className="text-xs text-gray-600 hover:text-gray-800 font-medium"
                >
                  Disable All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={handleResetToDefaults}
                  className="text-xs text-green-600 hover:text-green-800 font-medium"
                >
                  Reset to Entity Default
                </button>
              </div>

              {/* Tolerance Settings */}
              {rulesConfig?.data?.tolerance_settings && (
                <div className="text-xs text-gray-500">
                  Tolerance: {(rulesConfig.data.tolerance_settings.percentage_tolerance * 100).toFixed(4)}% |
                  Absolute: ₹{rulesConfig.data.tolerance_settings.absolute_tolerance}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Validation Results */}
      {validationResult && (
        <div className="card" id="validation-results">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📊 Validation Results</h2>
          
          {/* Summary Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-gray-900">{validationResult.total_rules || 6}</div>
              <div className="text-sm text-gray-500">Total Rules</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-green-600">{validationResult.rules_passed || 0}</div>
              <div className="text-sm text-green-600">Rules Passed</div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-red-600">{validationResult.rules_failed || 0}</div>
              <div className="text-sm text-red-600">Rules Failed</div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-600">
                {validationResult.rules_passed && validationResult.total_rules 
                  ? Math.round((validationResult.rules_passed / validationResult.total_rules) * 100)
                  : 0}%
              </div>
              <div className="text-sm text-blue-600">Success Rate</div>
            </div>
          </div>

          {/* Action Buttons for Validation Results */}
          {validationResult.rules_failed > 0 && (
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800 mb-4">
                ⚠️ Some validation rules failed. You can either review and fix the issues, or proceed to the next step.
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={handleRejectAndReview}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <DocumentTextIcon className="h-5 w-5" />
                  <span>Review Issues</span>
                </button>
                <button
                  onClick={handleIgnoreAndContinue}
                  className="btn-primary flex items-center space-x-2"
                >
                  <CheckCircleIcon className="h-5 w-5" />
                  <span>Ignore & Continue</span>
                </button>
              </div>
            </div>
          )}

          {/* AI Insights Generation - COMMENTED OUT */}
          {/* {validationResult.rules_failed > 0 && (
            <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-300 rounded-lg">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <LightBulbIcon className="h-6 w-6 text-purple-600 mt-1" />
                  <div>
                    <h4 className="text-sm font-semibold text-purple-900">🤖 AI-Powered Insights</h4>
                    <p className="text-sm text-purple-700 mt-1">
                      Get detailed AI analysis of why validation failed and actionable recommendations to fix the issues
                    </p>
                    <ul className="text-xs text-purple-600 mt-2 space-y-1">
                      <li>✓ Root cause analysis for each failed rule</li>
                      <li>✓ Step-by-step fix recommendations</li>
                      <li>✓ Examples and common patterns</li>
                      <li>✓ Prioritized action plan</li>
                    </ul>
                  </div>
                </div>
                <button
                  onClick={handleGenerateInsights}
                  disabled={generateInsightsMutation.isLoading}
                  className="btn-primary bg-purple-600 hover:bg-purple-700 flex items-center space-x-2"
                >
                  {generateInsightsMutation.isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <LightBulbIcon className="h-5 w-5" />
                      <span>Generate AI Insights</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )} */}

          {/* Display Insights Report if Available - COMMENTED OUT */}
          {/* {insightsReport && (
            <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <LightBulbIcon className="h-6 w-6 text-green-600" />
                  <div>
                    <h4 className="text-sm font-semibold text-green-900">✅ AI Insights Report Available</h4>
                    <p className="text-sm text-green-700">
                      Comprehensive analysis with root causes, recommendations, and action plan
                    </p>
                  </div>
                </div>
                <button
                  onClick={async () => {
                    try {
                      const insightsFilename = getFilename(insightsReport);
                      const response = await apiService.downloadEntityFile(
                        getCompanyName(),
                        'adjusted_trialbalance',
                        insightsFilename
                      );
                      const url = window.URL.createObjectURL(new Blob([response.data]));
                      const link = document.createElement('a');
                      link.href = url;
                      link.setAttribute('download', insightsFilename);
                      document.body.appendChild(link);
                      link.click();
                      link.remove();
                      window.URL.revokeObjectURL(url);
                      toast.success('Downloaded AI Insights Report');
                    } catch (error) {
                      toast.error('Failed to download insights report');
                    }
                  }}
                  className="btn-primary bg-green-600 hover:bg-green-700 flex items-center space-x-2"
                >
                  <ArrowDownTrayIcon className="h-5 w-5" />
                  <span>Download Insights</span>
                </button>
              </div>
            </div>
          )} */}

          {/* Download Validation Report */}
          {validationResult.report_path && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Validation Report</h4>
                  <p className="text-sm text-gray-500">Detailed 6-rules validation report with all findings</p>
                </div>
                <button
                  onClick={handleDownloadValidationReport}
                  className="btn-primary flex items-center space-x-2"
                >
                  <DocumentTextIcon className="h-5 w-5" />
                  <span>Download Report</span>
                </button>
              </div>
            </div>
          )}
          
          {/* Fallback: Show download button even if report_path not in result */}
          {!validationResult.report_path && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-blue-900">Download Validation Report</h4>
                  <p className="text-sm text-blue-700">If the validation report was generated, you can download it here</p>
                </div>
                <button
                  onClick={handleDownloadValidationReport}
                  className="btn-primary flex items-center space-x-2"
                >
                  <DocumentTextIcon className="h-5 w-5" />
                  <span>Try Download</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <div className="card">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/step4')}
            className="btn-secondary"
          >
            ← Back to Step 4
          </button>
          
          <button
            onClick={() => navigate('/step6')}
            className="btn-primary"
          >
            Continue to Step 6 →
          </button>
        </div>
      </div>

      {/* Issues Modal */}
      {showIssuesModal && validationResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="bg-red-50 border-b border-red-200 px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-red-900 flex items-center">
                <DocumentTextIcon className="h-6 w-6 mr-2" />
                Validation Issues - {validationResult.rules_failed} Rule(s) Failed
              </h3>
              <button
                onClick={() => setShowIssuesModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-8rem)]">
              {validationResult.summary?.failed_rules && validationResult.summary.failed_rules.length > 0 ? (
                <div className="space-y-4">
                  {validationResult.summary.failed_rules.map((rule: any, index: number) => (
                    <div key={index} className="border border-red-200 rounded-lg p-4 bg-red-50">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-semibold text-red-900">
                            Rule {rule.rule_number}: {rule.rule_name}
                          </h4>
                          <p className="text-sm text-red-700 mt-1">{rule.details}</p>
                        </div>
                        <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded">
                          FAILED
                        </span>
                      </div>
                      
                      {rule.has_violations && validationResult.summary?.violations_count?.[rule.rule_key] > 0 && (
                        <div className="mt-3 pt-3 border-t border-red-200">
                          <p className="text-sm font-medium text-red-800 mb-2">
                            {validationResult.summary.violations_count[rule.rule_key]} violation(s) found
                          </p>
                          <p className="text-xs text-red-600">
                            See the Excel validation report for complete details
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No detailed information available. Please check the validation report.</p>
                </div>
              )}

              {/* Download Report Button */}
              {validationResult.report_path && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={handleDownloadValidationReport}
                    className="w-full btn-primary flex items-center justify-center space-x-2"
                  >
                    <ArrowDownTrayIcon className="h-5 w-5" />
                    <span>Download Complete Validation Report</span>
                  </button>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end space-x-3">
              <button
                onClick={() => setShowIssuesModal(false)}
                className="btn-secondary"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowIssuesModal(false);
                  handleIgnoreAndContinue();
                }}
                className="btn-primary"
              >
                Ignore & Continue to Step 6
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Step5ValidateRules;
