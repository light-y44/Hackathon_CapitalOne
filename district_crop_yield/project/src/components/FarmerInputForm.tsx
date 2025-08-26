import React, { useState } from 'react';
import { FarmerDetails } from '../types';
import { Edit3, ChevronDown } from 'lucide-react';

interface FarmerInputFormProps {
  onSubmit: (data: FarmerDetails) => void;
  isCollapsed: boolean;
  farmerData?: FarmerDetails;
  onEdit: () => void;
}

const districts = ['Ashoknagar', 'Bhopal', 'Indore', 'Gwalior', 'Jabalpur'];
const crops = ['Wheat', 'Rice', 'Maize', 'Soybean', 'Cotton'];
const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

const FarmerInputForm: React.FC<FarmerInputFormProps> = ({ onSubmit, isCollapsed, farmerData, onEdit }) => {
  const [formData, setFormData] = useState<FarmerDetails>({
    district: 'Ashoknagar',
    crop: 'Wheat',
    loanAmount: 40000,
    interestRate: 7,
    farmArea: 2,
    nonFarmIncome: 2500,
    insurancePremium: 2000,
    tenure: 12,
    inputCost: 35000,
    monthlyExpenses: 10000,
    year: 2024,
    month: 'February'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (field: keyof FarmerDetails, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (isCollapsed && farmerData) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 border border-green-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-green-600 font-semibold">📋</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Farmer Loan Details</h3>
              <p className="text-sm text-gray-600">
                {farmerData.district} • {farmerData.crop} • ₹{farmerData.loanAmount.toLocaleString()}
              </p>
            </div>
          </div>
          <button
            onClick={onEdit}
            className="flex items-center space-x-2 px-3 py-2 bg-green-50 hover:bg-green-100 text-green-700 rounded-lg transition-colors duration-200"
          >
            <Edit3 size={16} />
            <span>Edit</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-green-100">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
          <span className="text-green-600 text-lg font-semibold">📋</span>
        </div>
        <h2 className="text-xl font-bold text-gray-900">Farmer Loan Details</h2>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">District:</label>
          <select
            value={formData.district}
            onChange={(e) => handleChange('district', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          >
            {districts.map(district => (
              <option key={district} value={district}>{district}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Crop:</label>
          <select
            value={formData.crop}
            onChange={(e) => handleChange('crop', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          >
            {crops.map(crop => (
              <option key={crop} value={crop}>{crop}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Loan Amount (₹):</label>
          <input
            type="number"
            value={formData.loanAmount}
            onChange={(e) => handleChange('loanAmount', parseInt(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Interest Rate (%):</label>
          <input
            type="number"
            step="0.1"
            value={formData.interestRate}
            onChange={(e) => handleChange('interestRate', parseFloat(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Area of Farm (acres):</label>
          <input
            type="number"
            value={formData.farmArea}
            onChange={(e) => handleChange('farmArea', parseInt(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Non-Farm Income (₹):</label>
          <input
            type="number"
            value={formData.nonFarmIncome}
            onChange={(e) => handleChange('nonFarmIncome', parseInt(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Insurance Premium (₹):</label>
          <input
            type="number"
            value={formData.insurancePremium}
            onChange={(e) => handleChange('insurancePremium', parseInt(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Tenure (months):</label>
          <input
            type="number"
            value={formData.tenure}
            onChange={(e) => handleChange('tenure', parseInt(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Input Cost (₹):</label>
          <input
            type="number"
            value={formData.inputCost}
            onChange={(e) => handleChange('inputCost', parseInt(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Monthly Expenses (₹):</label>
          <input
            type="number"
            value={formData.monthlyExpenses}
            onChange={(e) => handleChange('monthlyExpenses', parseInt(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Year:</label>
          <input
            type="number"
            value={formData.year}
            onChange={(e) => handleChange('year', parseInt(e.target.value))}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Month:</label>
          <select
            value={formData.month}
            onChange={(e) => handleChange('month', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
          >
            {months.map(month => (
              <option key={month} value={month}>{month}</option>
            ))}
          </select>
        </div>

        <div className="col-span-1 md:col-span-2">
          <button
            type="submit"
            className="w-full bg-gradient-to-r from-green-600 to-green-700 text-white py-4 px-6 rounded-lg font-semibold hover:from-green-700 hover:to-green-800 transition-all duration-300 transform hover:scale-[1.02] shadow-lg"
          >
            Submit
          </button>
        </div>
      </form>
    </div>
  );
};

export default FarmerInputForm;