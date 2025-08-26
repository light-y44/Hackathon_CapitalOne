import React from 'react';
import { FarmerDetails, BaselineSummary, Recommendation } from '../types';
import { ArrowLeft, Calculator, TrendingUp, Target, DollarSign, BarChart3, PieChart } from 'lucide-react';

interface DetailedAnalysisProps {
  farmerData: FarmerDetails;
  summary: BaselineSummary;
  recommendations: Recommendation[];
  onBack: () => void;
}

const DetailedAnalysis: React.FC<DetailedAnalysisProps> = ({ farmerData, summary, recommendations, onBack }) => {
  const calculateEMI = () => {
    const principal = farmerData.loanAmount;
    const rate = farmerData.interestRate / 100 / 12;
    const tenure = farmerData.tenure;
    return Math.round((principal * rate * Math.pow(1 + rate, tenure)) / (Math.pow(1 + rate, tenure) - 1));
  };

  const emi = calculateEMI();

  // Calculate detailed financial metrics
  const predictedPrice = summary.cropPrice; // Rs per quintal
  const predictedYield = summary.cropYield; // quintal per acre
  const revenuePerAcre = predictedPrice * predictedYield;
  const grossRevenueFarming = revenuePerAcre * farmerData.farmArea;
  const marketingExp = grossRevenueFarming * 0.02;
  const netFarmIncome = grossRevenueFarming - farmerData.inputCost - farmerData.insurancePremium - marketingExp;
  const totalIncome = netFarmIncome + (farmerData.nonFarmIncome * 6);
  const surplusBeforeLoan = totalIncome - (farmerData.monthlyExpenses * 6);
  const totalEMI = emi * 6;
  const surplusAfterLoan = surplusBeforeLoan - totalEMI;

  // Chart data
  const totalRevenue = grossRevenueFarming + (farmerData.nonFarmIncome * 6);
  const farmingCosts = farmerData.inputCost + farmerData.insurancePremium + marketingExp;
  const householdExpense = farmerData.monthlyExpenses * 6;
  const shortfall = Math.max(0, (farmingCosts + householdExpense + totalEMI) - totalRevenue);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <button
            onClick={onBack}
            className="flex items-center space-x-2 text-green-600 hover:text-green-700 transition-colors"
          >
            <ArrowLeft size={20} />
            <span>Back to Summary</span>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Detailed Report Section */}
          <div className="lg:col-span-2 space-y-8">
            <div className="bg-white rounded-xl shadow-lg p-6 border border-green-100">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Calculator className="text-blue-600" size={20} />
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Detailed Financial Analysis</h2>
              </div>

              {/* Farmer Details */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-gray-900 mb-4">Farmer Profile</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="font-medium">District:</span> {farmerData.district}</div>
                  <div><span className="font-medium">Crop:</span> {farmerData.crop}</div>
                  <div><span className="font-medium">Farm Area:</span> {farmerData.farmArea} acres</div>
                  <div><span className="font-medium">Season:</span> {farmerData.month} {farmerData.year}</div>
                </div>
              </div>

              {/* Loan Calculations */}
              <div className="bg-red-50 rounded-lg p-4 mb-6 border border-red-200">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                  <DollarSign className="mr-2 text-red-600" size={18} />
                  Loan Details & EMI Calculation
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Principal Amount:</span>
                      <span className="font-bold">₹{farmerData.loanAmount.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Interest Rate:</span>
                      <span className="font-bold">{farmerData.interestRate}% per annum</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Tenure:</span>
                      <span className="font-bold">{farmerData.tenure} months</span>
                    </div>
                    <div className="flex justify-between border-t pt-2">
                      <span>Monthly EMI:</span>
                      <span className="font-bold text-red-600">₹{emi.toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Total Interest:</span>
                      <span className="font-bold">₹{((emi * farmerData.tenure) - farmerData.loanAmount).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Payable:</span>
                      <span className="font-bold">₹{(emi * farmerData.tenure).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Detailed Financial Calculations */}
              <div className="space-y-6">
                {/* 1. Gross Revenue from Farming */}
                <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                    <TrendingUp className="mr-2 text-green-600" size={18} />
                    1. Gross Revenue from Farming
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    The gross revenue is the total amount earned from farming activity done on your specified land area. 
                    The amount is calculated based on predicted price, predicted yield and input area of farming. 
                    This is the amount that you are expected to receive from your crops post harvest.
                  </p>
                  <div className="bg-white p-3 rounded border mb-3">
                    <div className="text-sm font-mono">
                      <div className="mb-2"><strong>Formula:</strong> Gross Revenue Farming = Predicted Price × Predicted Yield × Input Area</div>
                      <div>Predicted Price = ₹{predictedPrice.toLocaleString()}/quintal</div>
                      <div>Predicted Yield = {predictedYield} quintal/acre</div>
                      <div>Revenue per acre = ₹{predictedPrice.toLocaleString()} × {predictedYield} = ₹{revenuePerAcre.toLocaleString()}</div>
                      <div>Input Area = {farmerData.farmArea} acres</div>
                      <div className="font-bold text-green-600 mt-2">
                        Gross Revenue = ₹{revenuePerAcre.toLocaleString()} × {farmerData.farmArea} = ₹{grossRevenueFarming.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 2. Net Farm Income */}
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    2. Net Farm Income
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    The net farm income is the amount left after deducting all the farm related expense like input cost 
                    (eg. seeds, fertilizers, equipment, etc), insurance premium and marketing expense. 
                    This amount reflects the actual earning from farming activity.
                  </p>
                  <div className="bg-white p-3 rounded border">
                    <div className="text-sm font-mono">
                      <div className="mb-2"><strong>Formula:</strong> Net farm income = Gross revenue - Input Cost - Premium - Marketing Exp</div>
                      <div>Gross revenue = ₹{grossRevenueFarming.toLocaleString()}</div>
                      <div>Input cost = ₹{farmerData.inputCost.toLocaleString()}</div>
                      <div>Premium = ₹{farmerData.insurancePremium.toLocaleString()}</div>
                      <div>Marketing exp (2% of revenue) = ₹{marketingExp.toLocaleString()}</div>
                      <div className="font-bold text-blue-600 mt-2">
                        Net Farm Income = ₹{grossRevenueFarming.toLocaleString()} - ₹{farmerData.inputCost.toLocaleString()} - ₹{farmerData.insurancePremium.toLocaleString()} - ₹{marketingExp.toLocaleString()} = ₹{netFarmIncome.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3. Total Income */}
                <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    3. Total Income
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    The total income is the collection of all your sources of income whether it be farming related income 
                    or non farm income which can include anything like you earn income from dairy, household work, 
                    labour work, employee etc. then all these incomes are summed up to get the total available income.
                  </p>
                  <div className="bg-white p-3 rounded border">
                    <div className="text-sm font-mono">
                      <div className="mb-2"><strong>Formula:</strong> Total income = Net farm income + Revenue from any off-farm activity</div>
                      <div>Monthly off-farm income = ₹{farmerData.nonFarmIncome.toLocaleString()}</div>
                      <div>Seasonal off-farm income (6 months) = ₹{(farmerData.nonFarmIncome * 6).toLocaleString()}</div>
                      <div>Net farm income = ₹{netFarmIncome.toLocaleString()}</div>
                      <div className="font-bold text-purple-600 mt-2">
                        Total Income = ₹{netFarmIncome.toLocaleString()} + ₹{(farmerData.nonFarmIncome * 6).toLocaleString()} = ₹{totalIncome.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 4. Surplus before loan */}
                <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    4. Surplus before loan or Net available
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    This amount is the total extra amount left with you when you have utilised your income for covering 
                    all your household expenses. This amount reflects your surplus before loan as is your saving if you 
                    did farming without any loan.
                  </p>
                  <div className="bg-white p-3 rounded border">
                    <div className="text-sm font-mono">
                      <div className="mb-2"><strong>Formula:</strong> Surplus before loan = Total income - Total household Expense</div>
                      <div>Monthly household expense = ₹{farmerData.monthlyExpenses.toLocaleString()}</div>
                      <div>Seasonal household expense (6 months) = ₹{(farmerData.monthlyExpenses * 6).toLocaleString()}</div>
                      <div>Total income = ₹{totalIncome.toLocaleString()}</div>
                      <div className="font-bold text-amber-600 mt-2">
                        Surplus before loan = ₹{totalIncome.toLocaleString()} - ₹{(farmerData.monthlyExpenses * 6).toLocaleString()} = ₹{surplusBeforeLoan.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 5. Monthly EMI */}
                <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    5. Monthly EMI
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    This is the monthly loan repayment charged to you for taking a loan for any activity. 
                    The amount is calculated based on the amount of loan taken (called principal), interest rate charged 
                    and the tenure of the loan.
                  </p>
                  <div className="bg-white p-3 rounded border">
                    <div className="text-sm font-mono">
                      <div className="mb-2"><strong>Formula:</strong> Monthly EMI = P × r × (1+r)^n / ((1+r)^n - 1)</div>
                      <div>P (Principal) = ₹{farmerData.loanAmount.toLocaleString()}</div>
                      <div>r (Monthly interest rate) = {(farmerData.interestRate/12).toFixed(4)}%</div>
                      <div>n (Tenure in months) = {farmerData.tenure}</div>
                      <div className="font-bold text-red-600 mt-2">
                        Monthly EMI = ₹{emi.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 6. Surplus after loan */}
                <div className={`${surplusAfterLoan >= 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'} rounded-lg p-4 border`}>
                  <h3 className="font-semibold text-gray-900 mb-4">
                    6. Surplus after loan
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    This amount reflects the total sum left after reducing all your expenses and repaying of complete loan 
                    from the total revenue from farm and off farm income. Positive amount shows you are in profit and you 
                    can easily repay loan whereas the negative amount shows that you have fallen short by that much amount 
                    and you either need to reduce your expense or need to extend your loan tenure.
                  </p>
                  <div className="bg-white p-3 rounded border">
                    <div className="text-sm font-mono">
                      <div className="mb-2"><strong>Formula:</strong> Surplus after loan = Net available - Total EMI</div>
                      <div>Net available = ₹{surplusBeforeLoan.toLocaleString()}</div>
                      <div>Monthly EMI = ₹{emi.toLocaleString()}</div>
                      <div>Seasonal EMI (6 months) = ₹{totalEMI.toLocaleString()}</div>
                      <div className={`font-bold mt-2 ${surplusAfterLoan >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        Surplus after loan = ₹{surplusBeforeLoan.toLocaleString()} - ₹{totalEMI.toLocaleString()} = ₹{surplusAfterLoan.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Financial Visualization */}
              <div className="bg-gray-50 rounded-lg p-4 mt-6 border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                  <BarChart3 className="mr-2 text-blue-600" size={18} />
                  Financial Breakdown
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Bar Chart Representation */}
                  <div className="bg-white p-4 rounded border">
                    <h4 className="font-medium text-gray-800 mb-4">Income vs Expenses</h4>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Total Revenue</span>
                          <span className="font-medium">₹{totalRevenue.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-6">
                          <div className="bg-green-500 h-6 rounded-full" style={{width: '100%'}}></div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Farming Costs</span>
                          <span className="font-medium">₹{farmingCosts.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-4">
                          <div className="bg-orange-500 h-4 rounded-full" style={{width: `${(farmingCosts/totalRevenue)*100}%`}}></div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Household Expenses</span>
                          <span className="font-medium">₹{householdExpense.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-4">
                          <div className="bg-blue-500 h-4 rounded-full" style={{width: `${(householdExpense/totalRevenue)*100}%`}}></div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Total EMI</span>
                          <span className="font-medium">₹{totalEMI.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-4">
                          <div className="bg-red-500 h-4 rounded-full" style={{width: `${(totalEMI/totalRevenue)*100}%`}}></div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Shortfall/Surplus Indicator */}
                  <div className="bg-white p-4 rounded border">
                    <h4 className="font-medium text-gray-800 mb-4">Financial Status</h4>
                    {shortfall > 0 ? (
                      <div className="text-center">
                        <div className="w-24 h-24 mx-auto mb-3 rounded-full bg-red-100 flex items-center justify-center">
                          <PieChart className="text-red-600" size={32} />
                        </div>
                        <div className="text-red-600 font-bold text-lg">Shortfall</div>
                        <div className="text-red-500 text-2xl font-bold">₹{shortfall.toLocaleString()}</div>
                        <p className="text-sm text-gray-600 mt-2">
                          Your expenses exceed your income by this amount
                        </p>
                      </div>
                    ) : (
                      <div className="text-center">
                        <div className="w-24 h-24 mx-auto mb-3 rounded-full bg-green-100 flex items-center justify-center">
                          <TrendingUp className="text-green-600" size={32} />
                        </div>
                        <div className="text-green-600 font-bold text-lg">Surplus</div>
                        <div className="text-green-500 text-2xl font-bold">₹{Math.abs(surplusAfterLoan).toLocaleString()}</div>
                        <p className="text-sm text-gray-600 mt-2">
                          You have this amount left after all expenses
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendations Section */}
          <div className="lg:col-span-1">
            <div className="space-y-6">
              {/* Recommendations Section */}
              <div className="bg-white rounded-xl shadow-lg p-6 border border-green-100 sticky top-8">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                    <Target className="text-purple-600" size={20} />
                  </div>
                  <h2 className="text-xl font-bold text-gray-900">Recommendations</h2>
                </div>

                <div className="space-y-4">
                  {recommendations.map((rec, index) => (
                    <div key={index} className="border border-blue-200 bg-blue-50 p-4 rounded-lg">
                      <div className="mb-2">
                        <span className="font-semibold text-blue-800">Option {index + 1}:</span>
                      </div>
                      <p className="text-gray-700 text-sm mb-3">{rec.option}</p>
                      <div className="mb-3">
                        <span className="font-semibold text-blue-800">Impact:</span>
                        <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                          rec.score_surplus > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          ₹{rec.score_surplus.toLocaleString()} surplus
                        </span>
                      </div>
                      <div>
                        <span className="font-semibold text-blue-800 text-sm">Key Benefits:</span>
                        <ul className="list-disc list-inside mt-1 space-y-1 text-xs text-gray-600">
                          {rec.details.message}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
                  <h3 className="font-semibold text-green-800 mb-2">Next Steps</h3>
                  <ul className="text-sm text-green-700 space-y-1">
                    <li>• Review all recommendation options</li>
                    <li>• Consult with local bank representative</li>
                    <li>• Consider seasonal cash flow patterns</li>
                    <li>• Plan for emergency fund allocation</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailedAnalysis;