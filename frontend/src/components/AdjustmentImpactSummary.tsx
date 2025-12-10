import React, { useState } from 'react';
import { formatCurrency } from '../utils/currencyFormatter';
import type { CurrencyInfo, FxRate } from '../types/currency';
import {
    ArrowTrendingUpIcon,
    ArrowTrendingDownIcon,
    ExclamationTriangleIcon,
    CheckCircleIcon,
    BanknotesIcon,
    BuildingLibraryIcon,
    ScaleIcon,
    ChartBarIcon,
    CurrencyDollarIcon,
    ChevronDownIcon,
    ChevronUpIcon,
} from '@heroicons/react/24/outline';

interface CategoryImpact {
    unaudited: number;
    adjusted: number;
    change: number;
    count: number;
}

interface MaterialChange {
    gl_code: string;
    description: string;
    category: string;
    unaudited: number;
    adjusted: number;
    change: number;
    pct_change?: number;
}

interface AdjustmentTypeImpact {
    adjustment_type: string;
    total_impact: number;
    count: number;
}

interface GLChange {
    gl_code: string;
    description: string;
    category: string;
    unaudited: number;
    adjusted: number;
    change: number;
}

interface ImpactSummaryData {
    entity: string;
    status: string;
    message?: string;
    summary?: {
        total_unaudited: number;
        total_adjusted: number;
        total_change: number;
        total_gl_codes: number;
        gl_codes_changed: number;
    };
    impact_by_category?: {
        Assets: CategoryImpact;
        Liabilities: CategoryImpact;
        Equity: CategoryImpact;
        Revenue: CategoryImpact;
        Expenses: CategoryImpact;
    };
    impact_by_adjustment_type?: AdjustmentTypeImpact[];
    material_changes?: MaterialChange[];
    gl_level_changes?: GLChange[];
}

interface AdjustmentDetail {
    account: string;
    debit: number;
    credit: number;
    description: string;
    schedule_iii_head: string;
    compliance_impact: string;
    adjustment_classification: string;
    compliance_standard: string;
    file_source: string;
}

interface AdjustmentAnalysisResponse {
    entity: string;
    total_adjustments: number;
    total_files: number;
    summary_by_classification: any[];
    summary_by_schedule_iii: any[];
    adjustments: AdjustmentDetail[];
}

interface Props {
    data: ImpactSummaryData;
    currencyInfo?: CurrencyInfo; // base/local currency
    selectedCurrency?: CurrencyInfo; // target currency to display
    fxRates?: FxRate[];
    convertValue?: (value: number) => number;
    selectedClassification?: string | null;
    adjustmentsData?: AdjustmentAnalysisResponse;
}

const AdjustmentImpactSummary: React.FC<Props> = ({
    data,
    currencyInfo,
    selectedCurrency,
    fxRates = [],
    convertValue,
    selectedClassification,
    adjustmentsData,
}) => {
    const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

    const effectiveCurrency = selectedCurrency || currencyInfo;
    const convert = (value: number): number => {
        if (convertValue) return convertValue(value);
        if (!currencyInfo || !selectedCurrency) return value;
        const baseCode = currencyInfo.default_currency.toUpperCase();
        const targetCode = selectedCurrency.default_currency.toUpperCase();
        if (baseCode === targetCode) return value;
        const rate = fxRates.find((r) => r.target_currency === targetCode);
        if (!rate) return value;
        return value * rate.rate;
    };

    // Create a mapping of GL codes to adjustment classifications
    const glToClassification = new Map<string, Set<string>>();
    if (adjustmentsData?.adjustments) {
        adjustmentsData.adjustments.forEach((adj) => {
            if (!glToClassification.has(adj.account)) {
                glToClassification.set(adj.account, new Set());
            }
            glToClassification.get(adj.account)?.add(adj.adjustment_classification);
        });
    }

    // Filter material changes and GL changes based on selected classification
    const filterByClassification = (glCode: string): boolean => {
        if (!selectedClassification || !adjustmentsData) return true;
        const classifications = glToClassification.get(glCode);
        return classifications ? classifications.has(selectedClassification) : false;
    };

    // Filter data if classification is selected
    const filteredGLChanges = selectedClassification && data.gl_level_changes
        ? data.gl_level_changes.filter(gl => filterByClassification(gl.gl_code))
        : data.gl_level_changes;
    if (data.status === 'not_applied') {
        return (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <div className="flex items-center gap-3">
                    <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600" />
                    <div>
                        <h3 className="text-sm font-semibold text-yellow-900 font-satoshi">
                            Impact Summary Not Available
                        </h3>
                        <p className="text-sm text-yellow-700 mt-1 font-satoshi">
                            {data.message || 'Please apply adjustments first to see the impact summary.'}
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    if (data.status === 'error') {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <div className="flex items-center gap-3">
                    <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                    <div>
                        <h3 className="text-sm font-semibold text-red-900 font-satoshi">
                            Error Loading Impact Summary
                        </h3>
                        <p className="text-sm text-red-700 mt-1 font-satoshi">
                            {data.message || 'Failed to load adjustment impact analysis.'}
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    if (!data.summary || !data.impact_by_category) {
        return null;
    }

    const getCategoryIcon = (category: string) => {
        switch (category) {
            case 'Assets':
                return <BanknotesIcon className="w-6 h-6" />;
            case 'Liabilities':
                return <BuildingLibraryIcon className="w-6 h-6" />;
            case 'Equity':
                return <ScaleIcon className="w-6 h-6" />;
            case 'Revenue':
                return <ChartBarIcon className="w-6 h-6" />;
            case 'Expenses':
                return <CurrencyDollarIcon className="w-6 h-6" />;
            default:
                return <ChartBarIcon className="w-6 h-6" />;
        }
    };

    const getCategoryColor = (category: string) => {
        switch (category) {
            case 'Assets':
                return 'from-blue-50 to-blue-100 border-blue-200 text-blue-700';
            case 'Liabilities':
                return 'from-red-50 to-red-100 border-red-200 text-red-700';
            case 'Equity':
                return 'from-purple-50 to-purple-100 border-purple-200 text-purple-700';
            case 'Revenue':
                return 'from-green-50 to-green-100 border-green-200 text-green-700';
            case 'Expenses':
                return 'from-orange-50 to-orange-100 border-orange-200 text-orange-700';
            default:
                return 'from-gray-50 to-gray-100 border-gray-200 text-gray-700';
        }
    };

    const toggleCategory = (category: string) => {
        setExpandedCategory(expandedCategory === category ? null : category);
    };

    const getCategoryGLChanges = (category: string): GLChange[] => {
        if (!filteredGLChanges) return [];
        return filteredGLChanges.filter((gl: GLChange) => gl.category === category);
    };

    return (
        <div className="space-y-6">
            {/* Header Stats */}
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200 p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-gray-900 font-satoshi">
                        Adjustment Impact Summary
                    </h3>
                    <CheckCircleIcon className="w-6 h-6 text-green-600" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <p className="text-xs text-gray-600 font-satoshi">Total GL Codes</p>
                        <p className="text-2xl font-bold text-gray-900 font-satoshi">
                            {data.summary.total_gl_codes}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-600 font-satoshi">GL Codes Changed</p>
                        <p className="text-2xl font-bold text-indigo-600 font-satoshi">
                            {data.summary.gl_codes_changed}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-600 font-satoshi">Unaudited Total</p>
                        <p className="text-xl font-bold text-gray-900 font-satoshi">
                            {formatCurrency(convert(data.summary.total_unaudited), effectiveCurrency)}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-600 font-satoshi">Adjusted Total</p>
                        <p className="text-xl font-bold text-gray-900 font-satoshi">
                            {formatCurrency(convert(data.summary.total_adjusted), effectiveCurrency)}
                        </p>
                    </div>
                </div>
            </div>

            {/* Impact by Category with Drill-Down */}
            <div>
                <h4 className="text-md font-bold text-gray-900 mb-3 font-satoshi">
                    Impact by Financial Statement Category
                    <span className="text-xs text-gray-500 ml-2 font-normal">(Click "View Changes" to see affected accounts)</span>
                </h4>
                <div className="space-y-4">
                    {Object.entries(data.impact_by_category).map(([category, impact]) => {
                        const isExpanded = expandedCategory === category;
                        const categoryChanges = getCategoryGLChanges(category);
                        const changedCount = categoryChanges.length;

                        return (
                            <div key={category} className="border border-gray-200 rounded-lg overflow-hidden">
                                {/* Category Card */}
                                <div className={`bg-gradient-to-br ${getCategoryColor(category)} border-b p-4`}>
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            {getCategoryIcon(category)}
                                            <h5 className="font-semibold text-sm font-satoshi">{category}</h5>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs font-medium px-2 py-1 bg-white bg-opacity-50 rounded-full font-satoshi">
                                                {impact.count} Total GLs
                                            </span>
                                            {changedCount > 0 && (
                                                <span className="text-xs font-medium px-2 py-1 bg-amber-100 text-amber-800 rounded-full font-satoshi">
                                                    {changedCount} Changed
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-3 gap-4 text-xs mb-3">
                                        <div>
                                            <span className="text-gray-700 font-satoshi block">Unaudited:</span>
                                            <span className="font-semibold font-satoshi text-sm">
                                                {formatCurrency(convert(impact.unaudited), effectiveCurrency)}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-gray-700 font-satoshi block">Adjusted:</span>
                                            <span className="font-semibold font-satoshi text-sm">
                                                {formatCurrency(convert(impact.adjusted), effectiveCurrency)}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-gray-700 font-medium font-satoshi block">Change:</span>
                                            <div className="flex items-center gap-1">
                                                {impact.change > 0 ? (
                                                    <ArrowTrendingUpIcon className="w-4 h-4" />
                                                ) : impact.change < 0 ? (
                                                    <ArrowTrendingDownIcon className="w-4 h-4" />
                                                ) : null}
                                                <span className={`font-bold font-satoshi text-sm ${impact.change > 0 ? 'text-green-700' :
                                                        impact.change < 0 ? 'text-red-700' : 'text-gray-700'
                                                    }`}>
                                                    {formatCurrency(convert(impact.change), effectiveCurrency)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* View Changes Button */}
                                    {changedCount > 0 && (
                                        <button
                                            onClick={() => toggleCategory(category)}
                                            className="w-full mt-2 px-4 py-2 bg-white bg-opacity-80 hover:bg-opacity-100 rounded-md flex items-center justify-center gap-2 transition-all text-sm font-medium font-satoshi"
                                        >
                                            {isExpanded ? (
                                                <>
                                                    <ChevronUpIcon className="w-4 h-4" />
                                                    Hide Changed Accounts
                                                </>
                                            ) : (
                                                <>
                                                    <ChevronDownIcon className="w-4 h-4" />
                                                    View {changedCount} Changed Account{changedCount !== 1 ? 's' : ''}
                                                </>
                                            )}
                                        </button>
                                    )}
                                </div>

                                {/* Expanded GL Changes Table */}
                                {isExpanded && categoryChanges.length > 0 && (
                                    <div className="bg-white">
                                        <div className="overflow-x-auto">
                                            <table className="min-w-full divide-y divide-gray-200">
                                                <thead className="bg-gray-50">
                                                    <tr>
                                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                            GL Code
                                                        </th>
                                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                            Description
                                                        </th>
                                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                            Unaudited
                                                        </th>
                                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                            Adjusted
                                                        </th>
                                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                            Change
                                                        </th>
                                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                            % Change
                                                        </th>
                                                    </tr>
                                                </thead>
                                                <tbody className="bg-white divide-y divide-gray-200">
                                                    {categoryChanges.map((gl, idx) => {
                                                        const pctChange = gl.unaudited !== 0
                                                            ? (gl.change / gl.unaudited) * 100
                                                            : 0;

                                                        return (
                                                            <tr key={idx} className="hover:bg-gray-50">
                                                                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 font-satoshi">
                                                                    {gl.gl_code}
                                                                </td>
                                                                <td className="px-4 py-3 text-sm text-gray-700 font-satoshi">
                                                                    <div className="max-w-xs truncate" title={gl.description}>
                                                                        {gl.description}
                                                                    </div>
                                                                </td>
                                                                <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900 font-satoshi">
                                                                    {formatCurrency(convert(gl.unaudited), effectiveCurrency)}
                                                                </td>
                                                                <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900 font-satoshi">
                                                                    {formatCurrency(convert(gl.adjusted), effectiveCurrency)}
                                                                </td>
                                                                <td className={`px-4 py-3 whitespace-nowrap text-sm text-right font-semibold font-satoshi ${gl.change > 0 ? 'text-green-700' :
                                                                        gl.change < 0 ? 'text-red-700' : 'text-gray-700'
                                                                    }`}>
                                                                    {formatCurrency(convert(gl.change), effectiveCurrency)}
                                                                </td>
                                                                <td className={`px-4 py-3 whitespace-nowrap text-sm text-right font-satoshi ${pctChange > 0 ? 'text-green-600' :
                                                                        pctChange < 0 ? 'text-red-600' : 'text-gray-600'
                                                                    }`}>
                                                                    {pctChange !== 0 ? `${pctChange.toFixed(1)}%` : '-'}
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                            </table>
                                        </div>
                                        <div className="bg-gray-50 px-4 py-2 text-xs text-gray-600 font-satoshi">
                                            Showing {categoryChanges.length} changed account{categoryChanges.length !== 1 ? 's' : ''} in {category}
                                        </div>
                                    </div>
                                )}

                                {isExpanded && categoryChanges.length === 0 && (
                                    <div className="bg-white p-4 text-center text-sm text-gray-500 font-satoshi">
                                        No changed accounts in this category
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Impact by Adjustment Type */}
            {data.impact_by_adjustment_type && data.impact_by_adjustment_type.length > 0 && (
                <div>
                    <h4 className="text-md font-bold text-gray-900 mb-3 font-satoshi">
                        Impact by Adjustment Type
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {data.impact_by_adjustment_type.map((adj, idx) => (
                            <div
                                key={idx}
                                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <h5 className="text-sm font-semibold text-gray-900 font-satoshi">
                                        {adj.adjustment_type}
                                    </h5>
                                    <span className="text-xs text-gray-500 font-satoshi">
                                        {adj.count} entries
                                    </span>
                                </div>
                                <p className="text-lg font-bold text-indigo-600 font-satoshi">
                                    {formatCurrency(convert(adj.total_impact), effectiveCurrency)}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdjustmentImpactSummary;
