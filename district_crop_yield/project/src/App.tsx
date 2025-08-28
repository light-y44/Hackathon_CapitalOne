import { useState } from 'react';
import FarmerInputForm from './components/FarmerInputForm';
import BaselineSummary from './components/BaselineSummary';
import AIChat from './components/AIChat';
import ThinkingSteps from './components/ThinkingSteps';
import DetailedAnalysis from './components/DetailedAnalysis';
import { FarmerDetails, BaselineSummary as BaselineSummaryType, Recommendation, ThinkingStep } from './types';
import { Wheat, Bot } from 'lucide-react';

function App() {
  const [farmerData, setFarmerData] = useState<FarmerDetails | null>(null);
  const [isFormCollapsed, setIsFormCollapsed] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [showDetailedAnalysis, setShowDetailedAnalysis] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [baselineSummary, setBaselineSummary] = useState<BaselineSummaryType | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  const flaskappRoute = 'http://127.0.0.1:5000';

  const handleFormSubmit = async (data: FarmerDetails) => {
    setFarmerData(data);
    setIsFormCollapsed(true);
    
    try {
        const res = await fetch(`${flaskappRoute}/api/submit_initial_inputs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        console.log("I am getting response")
        if (! res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }

        const result = await res.json();
        const baselinedata = result.baseline;
        const recommendationsData: Recommendation[] = result.recommendations;

        console.log("Decoded result:", result);

        setBaselineSummary({
          grossRevenue: baselinedata.gross_revenue,
          netFarmIncome: baselinedata.net_farm_income,
          totalAvailable: baselinedata.total_available,
          surplusBeforeLoan: baselinedata.surplus_before_loan,
          surplusAfterLoan: baselinedata.surplus_after_loan,
          cropYield: baselinedata.predicted_yield,
          cropPrice: baselinedata.predicted_price
        });

        setRecommendations(recommendationsData)

        console.log("Success:", result);

        // Simulate processing
        setTimeout(() => {
          setShowSummary(true);
        }, 1000);

    } catch (error) {
        console.error("Error submitting form:", error);
    }
  };

  const handleEditForm = () => {
    setIsFormCollapsed(false);
    setShowSummary(false);
  };

  const handleViewDetailedAnalysis = () => {
    setShowDetailedAnalysis(true);
  };

  const handleBackFromDetailed = () => {
    setShowDetailedAnalysis(false);
  };

  if (showDetailedAnalysis && farmerData && baselineSummary) {
    return (
      <DetailedAnalysis
        farmerData={farmerData}
        summary={baselineSummary || undefined}
        recommendations={recommendations}
        onBack={handleBackFromDetailed}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-green-100">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-r from-green-600 to-green-700 rounded-xl flex items-center justify-center">
              <Wheat className="text-white" size={24} />
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-900">Krishi Salah</h1>
              <p className="text-sm text-gray-600">Aapka Krishi Salahkaar!</p>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Form and Summary */}
          <div className="lg:col-span-1 flex flex-col justify-between space-y-6">
            <FarmerInputForm
              onSubmit={handleFormSubmit}
              isCollapsed={isFormCollapsed}
              farmerData={farmerData || undefined}
              onEdit={handleEditForm}
            />
            
            {showSummary && baselineSummary && (
              <BaselineSummary
                summary={baselineSummary}
                recommendations={recommendations}
                onViewDetailed={handleViewDetailedAnalysis}
              />
            )}
          </div>

          {/* Right Column - AI Chat and Thinking Steps */}
          <div className="lg:col-span-2 flex flex-col max-h-[calc(100vh-200px)]">
            <div className='mb-6'>
              <AIChat onThinkingStepsUpdate={setThinkingSteps} />
            </div>
            <div className='flex-1 overflow-y-auto'>
              <ThinkingSteps steps={thinkingSteps} />
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-green-100 mt-16">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-center space-x-2 text-gray-600">
            <Bot size={20} className="text-green-600" />
            <span className="text-sm">Powered by Agricultural AI • Designed for Farmers</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;