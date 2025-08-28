import React from 'react';
import { BaselineSummary as BaselineSummaryType, Recommendation } from '../types';
import { TrendingUp, DollarSign, PieChart, BarChart3, ArrowRight } from 'lucide-react';

interface BaselineSummaryProps {
  summary: BaselineSummaryType;
  recommendations: Recommendation[];
  onViewDetailed: () => void;
}

const BaselineSummary: React.FC<BaselineSummaryProps> = ({ summary, recommendations, onViewDetailed }) => {
  return (
    <div className="space-y-6">
      {/* Summary Section */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-green-100">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <BarChart3 className="text-blue-600" size={20} />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Summary</h2>
          </div>
          <button
            onClick={onViewDetailed}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors duration-200"
          >
            <span>View Detailed Analysis</span>
            <ArrowRight size={16} />
          </button>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="mr-2 text-green-600" size={18} />
            Baseline Financials
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-3 rounded-lg border">
              <span className="text-sm text-gray-600">Gross Revenue:</span>
              <p className="font-bold text-lg text-green-600">₹{summary.grossRevenue.toLocaleString()}</p>
            </div>
            <div className="bg-white p-3 rounded-lg border">
              <span className="text-sm text-gray-600">Net Available Before Loan:</span>
              <p className="font-bold text-lg text-blue-600">₹{summary.surplusBeforeLoan.toLocaleString()}</p>
            </div>
            <div className="bg-white p-3 rounded-lg border">
              <span className="text-sm text-gray-600">Net Farm Income:</span>
              <p className="font-bold text-lg text-emerald-600">₹{summary.netFarmIncome.toLocaleString()}</p>
            </div>
            <div className="bg-white p-3 rounded-lg border">
              <span className="text-sm text-gray-600">Surplus After Loan:</span>
              <p className="font-bold text-lg text-amber-600">₹{summary.surplusAfterLoan.toLocaleString()}</p>
            </div>
            <div className="bg-white p-3 rounded-lg border md:col-span-2">
              <span className="text-sm text-gray-600">Total Available:</span>
              <p className="font-bold text-xl text-purple-600">₹{summary.totalAvailable.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};

export default BaselineSummary;