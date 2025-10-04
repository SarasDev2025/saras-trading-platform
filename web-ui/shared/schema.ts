// Shared schema types for frontend

export interface Portfolio {
  id: string;
  name: string;
  description?: string;
  currency: string;
  total_value: number;
  cash_balance: number;
  // Legacy camelCase properties for backward compatibility
  totalValue?: string;
  cashAvailable?: string;
  dayPnL?: string;
  dayPnLPercent?: string;
}

export interface CashBalanceResponse {
  portfolio_id: string;
  cash_balance: number;
  buying_power: number;
  total_value: number;
}

export interface AddFundsRequest {
  portfolio_id: string;
  amount: number;
}

export interface AddFundsResponse {
  portfolio_id: string;
  cash_balance: number;
  total_value: number;
  amount_added: number;
}
