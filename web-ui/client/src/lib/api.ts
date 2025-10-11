import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from "axios";

console.log("VITE_API_BASE_URL =", import.meta.env.VITE_API_BASE_URL);

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: any) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear invalid token
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      // Redirect to login if needed
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// API Response types
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// Auth functions
export const authAPI = {
  login: async (credentials: { email: string; password: string }) => {
    const response = await api.post<APIResponse<{ access_token: string; refresh_token: string }>>(
      "/auth/login", 
      credentials
    );
    return response.data;
  },
  
  register: async (userData: { 
    email: string; 
    password: string; 
    username: string;
    first_name?: string;
    last_name?: string;
  }) => {
    const response = await api.post<APIResponse>("/auth/register", userData);
    return response.data;
  },
  
  logout: async () => {
    const response = await api.post<APIResponse>("/auth/logout");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    return response.data;
  },
  
  refreshToken: async () => {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) throw new Error("No refresh token");
    
    const response = await api.post<APIResponse<{ access_token: string }>>(
      "/auth/refresh", 
      { refresh_token: refreshToken }
    );
    return response.data;
  }
};

// Trading API functions
export const tradingAPI = {
  // Broker management
  connectBroker: async (credentials: {
    broker_type: string;
    api_key: string;
    secret: string;
    paper_trading: boolean;
  }, broker_name: string) => {
    const response = await api.post<APIResponse>(
      `/trading/brokers/connect?broker_name=${broker_name}`, 
      credentials
    );
    return response.data;
  },
  
  listBrokers: async () => {
    const response = await api.get<APIResponse>("/trading/brokers");
    return response.data;
  },
  
  disconnectBroker: async (broker_name: string) => {
    const response = await api.delete<APIResponse>(`/trading/brokers/${broker_name}`);
    return response.data;
  },
  
  // Account info
  getAccountInfo: async (broker_name: string) => {
    const response = await api.get<APIResponse>(`/trading/account/${broker_name}`);
    return response.data;
  },
  
  getPositions: async (broker_name: string) => {
    const response = await api.get<APIResponse>(`/trading/positions/${broker_name}`);
    return response.data;
  },
  
  getBalance: async (broker_name: string) => {
    const response = await api.get<APIResponse>(`/trading/balance/${broker_name}`);
    return response.data;
  },
  
  // Trading operations
  placeOrder: async (order: {
    portfolio_id: string;
    asset_id: string;
    symbol: string;
    side: 'buy' | 'sell';
    quantity: number;
    order_type: 'market' | 'limit' | 'stop' | 'stop_limit';
    price?: number;
    broker_name: string;
    notes?: string;
  }) => {
    const response = await api.post<APIResponse>("/trading/orders", order);
    return response.data;
  },
  
  getOrderStatus: async (broker_name: string, order_id: string) => {
    const response = await api.get<APIResponse>(`/trading/orders/${broker_name}/${order_id}`);
    return response.data;
  },
  
  cancelOrder: async (broker_name: string, order_id: string) => {
    const response = await api.delete<APIResponse>(`/trading/orders/${broker_name}/${order_id}`);
    return response.data;
  },
  
  // Market data
  getMarketData: async (symbols: string[], broker_name: string) => {
    const response = await api.post<APIResponse>("/trading/market-data", {
      symbols,
      broker_name
    });
    return response.data;
  },
  
  getHistoricalData: async (symbol: string, period: string, broker_name: string) => {
    const response = await api.post<APIResponse>("/trading/historical-data", {
      symbol,
      period,
      broker_name
    });
    return response.data;
  },
  
  // Transactions
  getTransactions: async (limit = 50, offset = 0) => {
    const response = await api.get<APIResponse>(
      `/trading/transactions?limit=${limit}&offset=${offset}`
    );
    return response.data;
  },
  
  getTransactionDetail: async (transaction_id: string) => {
    const response = await api.get<APIResponse>(`/trading/transactions/${transaction_id}`);
    return response.data;
  },
  
  getTradingStats: async (portfolio_id?: string) => {
    const url = portfolio_id 
      ? `/trading/stats?portfolio_id=${portfolio_id}`
      : "/trading/stats";
    const response = await api.get<APIResponse>(url);
    return response.data;
  },
  
  getRecentActivity: async (limit = 10) => {
    const response = await api.get<APIResponse>(
      `/trading/recent-activity?limit=${limit}`
    );
    return response.data;
  },
  
  // Portfolio sync
  syncPositions: async (broker_name: string, portfolio_id: string) => {
    const response = await api.post<APIResponse>(
      `/trading/sync-positions/${broker_name}/${portfolio_id}`
    );
    return response.data;
  },
  
  // Health check
  healthCheck: async () => {
    const response = await api.get<APIResponse>("/trading/health");
    return response.data;
  }
};

// Portfolio API functions
export const portfolioAPI = {
  getPortfolios: async () => {
    const response = await api.get<APIResponse>("/portfolios");
    return response.data;
  },

  createPortfolio: async (portfolio: {
    name: string;
    description?: string;
    currency?: string;
  }) => {
    const response = await api.post<APIResponse>("/portfolios", portfolio);
    return response.data;
  },

  getPortfolio: async (portfolio_id: string) => {
    const response = await api.get<APIResponse>(`/portfolios/${portfolio_id}`);
    return response.data;
  },

  updatePortfolio: async (portfolio_id: string, updates: {
    name?: string;
    description?: string;
  }) => {
    const response = await api.put<APIResponse>(`/portfolios/${portfolio_id}`, updates);
    return response.data;
  },

  deletePortfolio: async (portfolio_id: string) => {
    const response = await api.delete<APIResponse>(`/portfolios/${portfolio_id}`);
    return response.data;
  },

  getPerformance: async (portfolio_id: string, timeframe: string = "1D") => {
    const response = await api.get<APIResponse>(`/portfolios/${portfolio_id}/performance?timeframe=${timeframe}`);
    return response.data;
  },

  createSnapshot: async (portfolio_id: string) => {
    const response = await api.post<APIResponse>(`/portfolios/${portfolio_id}/performance/snapshot`);
    return response.data;
  }
};

// User API functions
export const userAPI = {
  getProfile: async () => {
    const response = await api.get<APIResponse>("/users/profile");
    return response.data;
  },

  updateProfile: async (updates: {
    first_name?: string;
    last_name?: string;
    phone?: string;
  }) => {
    const response = await api.put<APIResponse>("/users/profile", updates);
    return response.data;
  }
};

// Algorithm API functions
export const algorithmAPI = {
  // List algorithms
  getAlgorithms: async (status?: string) => {
    const url = status
      ? `/api/v1/algorithms?status=${status}`
      : '/api/v1/algorithms';
    const response = await api.get<APIResponse>(url);
    return response.data;
  },

  // Get single algorithm
  getAlgorithm: async (algorithm_id: string) => {
    const response = await api.get<APIResponse>(`/api/v1/algorithms/${algorithm_id}`);
    return response.data;
  },

  // Create algorithm
  createAlgorithm: async (algorithm: {
    name: string;
    strategy_code: string;
    parameters?: Record<string, any>;
    auto_run?: boolean;
    execution_interval?: string;
    max_positions?: number;
    risk_per_trade?: number;
  }) => {
    const response = await api.post<APIResponse>('/api/v1/algorithms', algorithm);
    return response.data;
  },

  // Update algorithm
  updateAlgorithm: async (algorithm_id: string, updates: {
    name?: string;
    strategy_code?: string;
    parameters?: Record<string, any>;
    auto_run?: boolean;
    execution_interval?: string;
    max_positions?: number;
    risk_per_trade?: number;
  }) => {
    const response = await api.put<APIResponse>(`/api/v1/algorithms/${algorithm_id}`, updates);
    return response.data;
  },

  // Delete algorithm
  deleteAlgorithm: async (algorithm_id: string) => {
    const response = await api.delete<APIResponse>(`/api/v1/algorithms/${algorithm_id}`);
    return response.data;
  },

  // Toggle algorithm status
  toggleAlgorithm: async (algorithm_id: string) => {
    const response = await api.post<APIResponse>(`/api/v1/algorithms/${algorithm_id}/toggle`);
    return response.data;
  },

  // Execute algorithm
  executeAlgorithm: async (algorithm_id: string, dry_run: boolean = false) => {
    const response = await api.post<APIResponse>(
      `/api/v1/algorithms/${algorithm_id}/execute?dry_run=${dry_run}`
    );
    return response.data;
  },

  // Get signals
  getSignals: async (algorithm_id: string, limit: number = 50) => {
    const response = await api.get<APIResponse>(
      `/api/v1/algorithms/${algorithm_id}/signals?limit=${limit}`
    );
    return response.data;
  },

  // Validate code
  validateCode: async (strategy_code: string) => {
    const response = await api.post<APIResponse>('/api/v1/algorithms/validate', {
      strategy_code,
    });
    return response.data;
  },

  // Run backtest
  runBacktest: async (algorithm_id: string, config: {
    start_date: string;
    end_date: string;
    initial_capital: number;
  }) => {
    const response = await api.post<APIResponse>(
      `/api/v1/algorithms/${algorithm_id}/backtest`,
      config
    );
    return response.data;
  },

  // Get backtest results
  getBacktestResults: async (algorithm_id: string, limit: number = 10) => {
    const response = await api.get<APIResponse>(
      `/api/v1/algorithms/${algorithm_id}/backtest-results?limit=${limit}`
    );
    return response.data;
  },

  // Get dashboard
  getDashboard: async () => {
    const response = await api.get<APIResponse>('/api/v1/algorithms/dashboard');
    return response.data;
  },

  // Visual/No-Code Algorithm Methods
  getVisualBlocks: async () => {
    const response = await api.get<APIResponse>('/api/v1/algorithms/visual-blocks');
    return response.data;
  },

  compileVisualAlgorithm: async (visual_config: any) => {
    const response = await api.post<APIResponse>('/api/v1/algorithms/visual/compile', visual_config);
    return response.data;
  },

  validateVisualAlgorithm: async (visual_config: any) => {
    const response = await api.post<APIResponse>('/api/v1/algorithms/visual/validate', visual_config);
    return response.data;
  },

  getVisualTemplates: async (category?: string, difficulty?: string) => {
    let url = '/api/v1/algorithms/visual-templates';
    const params = [];
    if (category) params.push(`category=${category}`);
    if (difficulty) params.push(`difficulty=${difficulty}`);
    if (params.length > 0) url += `?${params.join('&')}`;

    const response = await api.get<APIResponse>(url);
    return response.data;
  },

  useVisualTemplate: async (template_id: string) => {
    const response = await api.post<APIResponse>(`/api/v1/algorithms/visual-templates/${template_id}/use`);
    return response.data;
  },
};

export default api;
