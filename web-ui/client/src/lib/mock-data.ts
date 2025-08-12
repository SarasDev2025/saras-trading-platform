// This file contains mock data structures for development
// In production, this would be replaced with actual API calls

export const mockPortfolioData = {
  totalValue: 2847392.18,
  dayPnL: 15847.32,
  dayPnLPercent: 0.56,
  cashAvailable: 184502.91,
  activePositions: 247,
};

export const mockPositions = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    quantity: 500,
    avgPrice: 178.32,
    currentPrice: 180.45,
    marketValue: 90225,
    unrealizedPnL: 1065,
    unrealizedPnLPercent: 1.19,
    assetType: "equity",
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corporation",
    quantity: 300,
    avgPrice: 384.12,
    currentPrice: 389.50,
    marketValue: 116850,
    unrealizedPnL: 1614,
    unrealizedPnLPercent: 1.40,
    assetType: "equity",
  },
  {
    symbol: "TSLA",
    name: "Tesla, Inc.",
    quantity: 200,
    avgPrice: 267.89,
    currentPrice: 265.30,
    marketValue: 53060,
    unrealizedPnL: -518,
    unrealizedPnLPercent: -0.97,
    assetType: "equity",
  },
];

export const mockTrades = [
  {
    id: "1",
    time: "09:34:12",
    symbol: "AAPL",
    side: "BUY" as const,
    quantity: 500,
    price: 178.32,
    value: 89160,
    status: "FILLED" as const,
  },
  {
    id: "2", 
    time: "09:28:45",
    symbol: "TSLA",
    side: "SELL" as const,
    quantity: 200,
    price: 267.89,
    value: 53578,
    status: "FILLED" as const,
  },
  {
    id: "3",
    time: "09:15:33",
    symbol: "MSFT",
    side: "BUY" as const,
    quantity: 300,
    price: 384.12,
    value: 115236,
    status: "PENDING" as const,
  },
];

export const mockStrategies = [
  {
    id: "1",
    name: "Momentum Strategy",
    description: "Buy high momentum stocks",
    type: "MOMENTUM",
    isActive: true,
    performance: { return: 12.5, sharpe: 1.8 },
  },
  {
    id: "2",
    name: "Mean Reversion",
    description: "Buy oversold stocks",
    type: "MEAN_REVERSION", 
    isActive: false,
    performance: { return: 8.3, sharpe: 1.2 },
  },
];

export const mockAlgorithms = [
  {
    id: "1",
    name: "RSI Signals",
    description: "Generate buy/sell signals based on RSI",
    language: "python",
    isActive: true,
    lastRun: new Date().toISOString(),
    performance: { accuracy: 0.73, trades: 45 },
  },
  {
    id: "2",
    name: "Moving Average Crossover",
    description: "SMA crossover strategy",
    language: "python",
    isActive: false,
    lastRun: null,
    performance: { accuracy: 0.68, trades: 32 },
  },
];
