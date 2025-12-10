import React, { useState } from 'react';
import {
    ChartBarIcon,
    DocumentChartBarIcon,
    ArrowTrendingUpIcon,
    ArrowTrendingDownIcon,
    ChevronDownIcon,
    ChevronUpIcon,
} from '@heroicons/react/24/outline';
import { formatCurrency } from '../utils/currencyFormatter';
import type { CurrencyInfo, FxRate } from '../types/currency';

interface FinalTBSummaryProps {
    entity: string;
    data: any;
    currencyInfo?: CurrencyInfo; // base/local currency
    selectedCurrency?: CurrencyInfo; // target currency to display
    fxRates?: FxRate[];
}

const FinalTBSummary: React.FC<FinalTBSummaryProps> = ({
    entity,
    data,
    currencyInfo,
    selectedCurrency,
    fxRates = [],
}) => {
    const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

    if (!data || data.status !== 'success') {
        return null;
    }

    const { summary, bspl_summary, indas_major_summary, period_columns } = data;

    const effectiveCurrency = selectedCurrency || currencyInfo;
    const convert = (value: number): number => {
        if (!currencyInfo || !selectedCurrency) return value;
        const baseCode = currencyInfo.default_currency.toUpperCase();
        const targetCode = selectedCurrency.default_currency.toUpperCase();
        if (baseCode === targetCode) return value;
        const rate = fxRates.find((r) => r.target_currency === targetCode);
        if (!rate) return value;
        return value * rate.rate;
    };

    // Calculate percentage change
    const calculatePercentChange = (change: number, original: number) => {
        if (original === 0) return 0;
        return (change / original) * 100;
    };

    const formatChange = (change: number, original: number) => {
        const pct = calculatePercentChange(change, original);
        const sign = change >= 0 ? '+' : '';
        return `${sign}${pct.toFixed(2)}%`;
    };

    const toggleCategory = (category: string) => {
        setExpandedCategory(expandedCategory === category ? null : category);
    };

    return (
        <div className="space-y-6">
            {/* Overall Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                    <div className="text-sm font-medium text-gray-600 font-satoshi">Total Accounts</div>
                    <div className="mt-2 text-2xl font-bold text-gray-900 font-satoshi">
                        {summary.total_accounts.toLocaleString()}
                    </div>
                </div>

                <div className="bg-blue-50 rounded-lg border border-blue-200 p-4 shadow-sm">
                    <div className="text-sm font-medium text-blue-700 font-satoshi">Total Unaudited</div>
                    <div className="mt-2 text-2xl font-bold text-blue-900 font-satoshi">
                        {formatCurrency(convert(summary.total_unaudited), effectiveCurrency)}
                    </div>
                </div>

                <div className="bg-green-50 rounded-lg border border-green-200 p-4 shadow-sm">
                    <div className="text-sm font-medium text-green-700 font-satoshi">Total Adjusted</div>
                    <div className="mt-2 text-2xl font-bold text-green-900 font-satoshi">
                        {formatCurrency(convert(summary.total_adjusted), effectiveCurrency)}
                    </div>
                </div>

                <div className={`rounded-lg border p-4 shadow-sm ${summary.total_change >= 0
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-red-50 border-red-200'
                    }`}>
                    <div className={`text-sm font-medium font-satoshi ${summary.total_change >= 0 ? 'text-emerald-700' : 'text-red-700'
                        }`}>
                        Net Change
                    </div>
                    <div className={`mt-2 text-2xl font-bold font-satoshi flex items-center gap-2 ${summary.total_change >= 0 ? 'text-emerald-900' : 'text-red-900'
                        }`}>
                        {summary.total_change >= 0 ? (
                            <ArrowTrendingUpIcon className="w-6 h-6" />
                        ) : (
                            <ArrowTrendingDownIcon className="w-6 h-6" />
                        )}
                        {formatCurrency(convert(Math.abs(summary.total_change)), effectiveCurrency)}
                    </div>
                    <div className={`text-sm font-satoshi ${summary.total_change >= 0 ? 'text-emerald-600' : 'text-red-600'
                        }`}>
                        {formatChange(summary.total_change, summary.total_unaudited)}
                    </div>
                </div>
            </div>

            {/* BSPL Breakdown */}
            {bspl_summary && Object.keys(bspl_summary).length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 font-satoshi flex items-center gap-2">
                        <ChartBarIcon className="w-6 h-6 text-purple-600" />
                        BSPL Category Breakdown
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(bspl_summary).map(([category, stats]: [string, any]) => (
                            <div key={category} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                                <div className="flex items-center justify-between mb-3">
                                    <h4 className="text-lg font-bold text-gray-900 font-satoshi">
                                        {category === 'BS' ? 'Balance Sheet' : category === 'PL' ? 'Profit & Loss' : category}
                                    </h4>
                                    <span className="text-sm text-gray-600 font-satoshi">
                                        {stats.count} accounts
                                    </span>
                                </div>

                                    <div className="space-y-2">
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm text-gray-600 font-satoshi">Unaudited:</span>
                                            <span className="text-sm font-medium text-gray-900 font-satoshi">
                                            {formatCurrency(convert(stats.unaudited), effectiveCurrency)}
                                            </span>
                                        </div>

                                        <div className="flex justify-between items-center">
                                            <span className="text-sm text-gray-600 font-satoshi">Adjusted:</span>
                                            <span className="text-sm font-medium text-gray-900 font-satoshi">
                                            {formatCurrency(convert(stats.adjusted), effectiveCurrency)}
                                            </span>
                                        </div>

                                    <div className="pt-2 border-t border-gray-200">
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm font-medium text-gray-700 font-satoshi">Change:</span>
                                            <div className="text-right">
                                                <div className={`text-sm font-bold font-satoshi ${stats.change >= 0 ? 'text-green-600' : 'text-red-600'
                                                    }`}>
                                                    {stats.change >= 0 ? '+' : ''}{formatCurrency(convert(stats.change), effectiveCurrency)}
                                                </div>
                                                <div className={`text-xs font-satoshi ${stats.change >= 0 ? 'text-green-600' : 'text-red-600'
                                                    }`}>
                                                    {formatChange(stats.change, stats.unaudited)}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Ind AS Major Category Breakdown with Drill-Down */}
            {indas_major_summary && indas_major_summary.length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 font-satoshi flex items-center gap-2">
                        <ChartBarIcon className="w-6 h-6 text-indigo-600" />
                        Ind AS Major Category Analysis
                        <span className="text-xs text-gray-500 ml-2 font-normal">(Click row to view changed accounts)</span>
                    </h3>

                    {/* Column Headers */}
                    <div className="grid grid-cols-6 gap-4 p-3 bg-gray-100 border-b-2 border-gray-300 font-satoshi">
                        <div className="col-span-1 text-xs font-semibold text-gray-700 uppercase tracking-wider">
                            Category
                        </div>
                        <div className="text-xs font-semibold text-gray-700 uppercase tracking-wider text-right">
                            Count
                        </div>
                        <div className="text-xs font-semibold text-gray-700 uppercase tracking-wider text-right">
                            Unaudited
                        </div>
                        <div className="text-xs font-semibold text-gray-700 uppercase tracking-wider text-right">
                            Adjusted
                        </div>
                        <div className="text-xs font-semibold text-gray-700 uppercase tracking-wider text-right">
                            Change
                        </div>
                        <div className="text-xs font-semibold text-gray-700 uppercase tracking-wider text-right">
                            % Change
                        </div>
                    </div>

                    <div className="space-y-2 mt-2">
                        {indas_major_summary.map((item: any, index: number) => {
                            const isExpanded = expandedCategory === item.category;
                            const hasChanges = item.changed_count > 0;

                            return (
                                <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                                    {/* Category Row - Clickable */}
                                    <div
                                        onClick={() => hasChanges && toggleCategory(item.category)}
                                        className={`grid grid-cols-6 gap-4 p-3 ${hasChanges ? 'cursor-pointer hover:bg-gray-50' : 'bg-gray-50'} transition-colors`}
                                    >
                                        <div className="col-span-1 flex items-center gap-2">
                                            <span className="text-sm font-medium text-gray-900 font-satoshi">
                                                {item.category}
                                            </span>
                                            {hasChanges && (
                                                isExpanded ? (
                                                    <ChevronUpIcon className="w-4 h-4 text-gray-500" />
                                                ) : (
                                                    <ChevronDownIcon className="w-4 h-4 text-gray-500" />
                                                )
                                            )}
                                        </div>
                                        <div className="text-sm text-gray-600 text-right font-satoshi flex items-center justify-end gap-1">
                                            {item.count}
                                            {hasChanges && (
                                                <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded">
                                                    {item.changed_count} changed
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-sm text-gray-900 text-right font-satoshi flex items-center justify-end">
                                            {formatCurrency(convert(item.unaudited), effectiveCurrency)}
                                        </div>
                                        <div className="text-sm text-gray-900 text-right font-satoshi flex items-center justify-end">
                                            {formatCurrency(convert(item.adjusted), effectiveCurrency)}
                                        </div>
                                        <div className={`text-sm text-right font-medium font-satoshi flex items-center justify-end ${item.change >= 0 ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            {item.change >= 0 ? '+' : ''}{formatCurrency(convert(item.change), effectiveCurrency)}
                                        </div>
                                        <div className={`text-sm text-right font-satoshi flex items-center justify-end ${item.change >= 0 ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            {formatChange(item.change, item.unaudited)}
                                        </div>
                                    </div>

                                    {/* Expanded GL Changes Table */}
                                    {isExpanded && item.gl_changes && item.gl_changes.length > 0 && (
                                        <div className="bg-gray-50 border-t border-gray-200">
                                            <div className="overflow-x-auto">
                                                <table className="min-w-full divide-y divide-gray-200">
                                                    <thead className="bg-white">
                                                        <tr>
                                                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                                GL Code
                                                            </th>
                                                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                                Description
                                                            </th>
                                                            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                                Unaudited
                                                            </th>
                                                            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                                Adjusted
                                                            </th>
                                                            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                                Change
                                                            </th>
                                                            <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider font-satoshi">
                                                                % Change
                                                            </th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="bg-white divide-y divide-gray-100">
                                                        {item.gl_changes.map((gl: any, glIdx: number) => {
                                                            const pctChange = gl.unaudited !== 0
                                                                ? (gl.change / gl.unaudited) * 100
                                                                : 0;

                                                            return (
                                                                <tr key={glIdx} className="hover:bg-gray-50">
                                                                    <td className="px-4 py-2 whitespace-nowrap text-xs font-medium text-gray-900 font-satoshi">
                                                                        {gl.gl_code}
                                                                    </td>
                                                                    <td className="px-4 py-2 text-xs text-gray-700 font-satoshi">
                                                                        <div className="max-w-xs truncate" title={gl.description}>
                                                                            {gl.description}
                                                                        </div>
                                                                    </td>
                                                                    <td className="px-4 py-2 whitespace-nowrap text-xs text-right text-gray-900 font-satoshi">
                                                                        {formatCurrency(convert(gl.unaudited), effectiveCurrency)}
                                                                    </td>
                                                                    <td className="px-4 py-2 whitespace-nowrap text-xs text-right text-gray-900 font-satoshi">
                                                                        {formatCurrency(convert(gl.adjusted), effectiveCurrency)}
                                                                    </td>
                                                                    <td className={`px-4 py-2 whitespace-nowrap text-xs text-right font-semibold font-satoshi ${gl.change > 0 ? 'text-green-700' :
                                                                        gl.change < 0 ? 'text-red-700' : 'text-gray-700'
                                                                        }`}>
                                                                        {formatCurrency(convert(gl.change), effectiveCurrency)}
                                                                    </td>
                                                                    <td className={`px-4 py-2 whitespace-nowrap text-xs text-right font-satoshi ${pctChange > 0 ? 'text-green-600' :
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
                                            <div className="bg-gray-100 px-4 py-2 text-xs text-gray-600 font-satoshi">
                                                Showing {item.gl_changes.length} changed account{item.gl_changes.length !== 1 ? 's' : ''} in {item.category}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default FinalTBSummary;
