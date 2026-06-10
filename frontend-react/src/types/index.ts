export interface Holding {
  ticker: string;
  name: string;
  shares: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  gain_loss: number;
  gain_loss_pct: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

export interface AddHoldingPayload {
  ticker: string;
  name: string;
  shares: number;
  avg_cost: number;
}

export interface ChatRequest {
  message: string;
  portfolio_holdings?: Omit<Holding, 'name'>[];
}

export interface ChatResponse {
  answer: string;
  sources: string[];
}
