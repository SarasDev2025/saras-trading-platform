import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tradingAPI, APIResponse } from '../lib/api';

// Broker management hooks
export const useBrokers = () => {
  return useQuery({
    queryKey: ['brokers'],
    queryFn: () => tradingAPI.listBrokers(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useConnectBroker = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ credentials, brokerName }: {
      credentials: {
        broker_type: string;
        api_key: string;
        secret: string;
        paper_trading: boolean;
      };
      brokerName: string;
    }) => tradingAPI.connectBroker(credentials, brokerName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['brokers'] });
    },
  });
};

export const useDisconnectBroker = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (brokerName: string) => tradingAPI.disconnectBroker(brokerName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['brokers'] });
    },
  });
};

// Account information hooks
export const useAccountInfo = (brokerName: string, enabled = true) => {
  return useQuery({
    queryKey: ['account', brokerName],
    queryFn: () => tradingAPI.getAccountInfo(brokerName),
    enabled: enabled && !!brokerName,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const usePositions = (brokerName: string, enabled = true) => {
  return useQuery({
    queryKey: ['positions', brokerName],
    queryFn: () => tradingAPI.getPositions(brokerName),
    enabled: enabled && !!brokerName,
    refetchInterval: 30 * 1000, // 30 seconds
  });
};

export const useBalance = (brokerName: string, enabled = true) => {
  return useQuery({
    queryKey: ['balance', brokerName],
    queryFn: () => tradingAPI.getBalance(brokerName),
    enabled: enabled && !!brokerName,
    refetchInterval: 30 * 1000, // 30 seconds
  });
};

// Trading operations hooks
export const usePlaceOrder = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (order: {
      portfolio_id: string;
      asset_id: string;
      symbol: string;
      side: 'buy' | 'sell';
      quantity: number;
      order_type: 'market' | 'limit' | 'stop' | 'stop_limit';
      price?: number;
      broker_name: string;
      notes?: string;
    }) => tradingAPI.placeOrder(order),
    onSuccess: (data, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['positions', variables.broker_name] });
      queryClient.invalidateQueries({ queryKey: ['balance', variables.broker_name] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['recent-activity'] });
    },
  });
};

export const useOrderStatus = (brokerName: string, orderId: string, enabled = true) => {
  return useQuery({
    queryKey: ['order-status', brokerName, orderId],
    queryFn: () => tradingAPI.getOrderStatus(brokerName, orderId),
    enabled: enabled && !!brokerName && !!orderId,
    refetchInterval: 5 * 1000, // 5 seconds
  });
};

export const useCancelOrder = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ brokerName, orderId }: { brokerName: string; orderId: string }) =>
      tradingAPI.cancelOrder(brokerName, orderId),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['order-status', variables.brokerName, variables.orderId] });
    },
  });
};

// Market data hooks
export const useMarketData = (symbols: string[], brokerName: string, enabled = true) => {
  return useQuery({
    queryKey: ['market-data', symbols, brokerName],
    queryFn: () => tradingAPI.getMarketData(symbols, brokerName),
    enabled: enabled && symbols.length > 0 && !!brokerName,
    refetchInterval: 10 * 1000, // 10 seconds
    staleTime: 5 * 1000, // 5 seconds
  });
};

export const useHistoricalData = (symbol: string, period: string, brokerName: string, enabled = true) => {
  return useQuery({
    queryKey: ['historical-data', symbol, period, brokerName],
    queryFn: () => tradingAPI.getHistoricalData(symbol, period, brokerName),
    enabled: enabled && !!symbol && !!brokerName,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Transaction hooks
export const useTransactions = (limit = 50, offset = 0) => {
  return useQuery({
    queryKey: ['transactions', limit, offset],
    queryFn: () => tradingAPI.getTransactions(limit, offset),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useTransactionDetail = (transactionId: string, enabled = true) => {
  return useQuery({
    queryKey: ['transaction', transactionId],
    queryFn: () => tradingAPI.getTransactionDetail(transactionId),
    enabled: enabled && !!transactionId,
  });
};

export const useTradingStats = (portfolioId?: string) => {
  return useQuery({
    queryKey: ['trading-stats', portfolioId],
    queryFn: () => tradingAPI.getTradingStats(portfolioId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useRecentActivity = (limit = 10) => {
  return useQuery({
    queryKey: ['recent-activity', limit],
    queryFn: () => tradingAPI.getRecentActivity(limit),
    refetchInterval: 30 * 1000, // 30 seconds
  });
};

// Portfolio sync hooks
export const useSyncPositions = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ brokerName, portfolioId }: { brokerName: string; portfolioId: string }) =>
      tradingAPI.syncPositions(brokerName, portfolioId),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['positions', variables.brokerName] });
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });
};

// Health check hook
export const useTradingHealth = () => {
  return useQuery({
    queryKey: ['trading-health'],
    queryFn: () => tradingAPI.healthCheck(),
    refetchInterval: 60 * 1000, // 1 minute
  });
};
