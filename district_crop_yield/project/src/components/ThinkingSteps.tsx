import React from 'react';
import { ThinkingStep } from '../types';
import { Brain, CheckCircle, Clock, Loader2 } from 'lucide-react';

interface ThinkingStepsProps {
  steps: ThinkingStep[];
}

const ThinkingSteps: React.FC<ThinkingStepsProps> = ({ steps }) => {
  const getStepIcon = (status: ThinkingStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'processing':
        return <Loader2 className="text-blue-500 animate-spin" size={20} />;
      case 'pending':
        return <Clock className="text-gray-400" size={20} />;
    }
  };

  const getStepColor = (status: ThinkingStep['status']) => {
    switch (status) {
      case 'completed':
        return 'border-green-200 bg-green-50';
      case 'processing':
        return 'border-blue-200 bg-blue-50';
      case 'pending':
        return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-green-100">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
          <Brain className="text-purple-600" size={20} />
        </div>
        <h2 className="text-xl font-bold text-gray-900">AI Thinking Process</h2>
      </div>

      <div className="space-y-3">
        {steps.map((step, index) => (
          <div key={step.id} className={`border rounded-lg p-4 transition-all duration-300 ${getStepColor(step.status)}`}>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-0.5">
                {getStepIcon(step.status)}
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-1">
                  {index + 1}. {step.step}
                </h3>
                <p className="text-gray-600 text-sm">{step.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ThinkingSteps;