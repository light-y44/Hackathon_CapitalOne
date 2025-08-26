export interface FarmerDetails {
  district: string;
  crop: string;
  loanAmount: number;
  interestRate: number;
  farmArea: number;
  nonFarmIncome: number;
  insurancePremium: number;
  tenure: number;
  inputCost: number;
  monthlyExpenses: number;
  year: number;
  month: string;
}

export interface BaselineSummary {
  grossRevenue: number;
  surplusBeforeLoan: number;
  netFarmIncome: number;
  surplusAfterLoan: number;
  totalAvailable: number;
  cropYield: number;
  cropPrice: number;
}

export interface Recommendation {
  option: string;
  score_surplus: number;
  details: {
    message : string;
  };
}

export interface ThinkingStep {
  id: string;
  step: string;
  description: string;
  status: 'pending' | 'processing' | 'completed';
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  audioUrl?: string;
}