import { useState, useCallback } from 'react';
import { Condition } from '../index';

interface Signal {
  date: string;
  type: 'buy' | 'sell';
  price: number;
  reason: string;
}

interface SignalStats {
  signalCount: number;
  buySignals: number;
  sellSignals: number;
  estimatedWinRate?: number;
  estimatedReturn?: number;
}

interface PriceDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  rsi?: number;
  sma_20?: number;
  sma_50?: number;
  ema_20?: number;
}

interface PortfolioSimulation {
  initial_capital: number;
  start_date: string;
  end_date: string;
  final_value: number;
  total_pnl_dollar: number;
  total_pnl_percent: number;
  current_position: {
    shares: number;
    symbol: string;
    value: number;
  };
  trades_executed: number;
  cash_remaining: number;
}

export function useSignalSimulation() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [stats, setStats] = useState<SignalStats | null>(null);
  const [portfolioSimulation, setPortfolioSimulation] = useState<PortfolioSimulation | null>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = useCallback(
    async (
      priceData: PriceDataPoint[],
      entryConditions: Condition[],
      exitConditions: Condition[],
      initialCapital?: number,
      startDate?: string,
      compositeData?: Array<{date: string; composite_index: number}>
    ) => {
      if (priceData.length === 0) {
        setSignals([]);
        setStats(null);
        setPortfolioSimulation(null);
        return;
      }

      setLoading(true);

      try {
        const requestBody = {
          price_data: priceData,
          entry_conditions: entryConditions,
          exit_conditions: exitConditions,
          initial_capital: initialCapital,
          start_date: startDate,
          composite_data: compositeData,  // NEW: Pass composite data for hybrid strategies
        };

        console.log('API Request - initial_capital:', initialCapital, 'start_date:', startDate);

        const response = await fetch('/api/v1/algorithms/visual/preview-signals', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify(requestBody),
        });

        const data = await response.json();

        if (data.success) {
          const detectedSignals: Signal[] = data.data.signals || [];
          setSignals(detectedSignals);

          // Calculate statistics
          const buyCount = detectedSignals.filter((s) => s.type === 'buy').length;
          const sellCount = detectedSignals.filter((s) => s.type === 'sell').length;

          // Calculate win rate and return if we have paired trades
          let estimatedWinRate: number | undefined;
          let estimatedReturn: number | undefined;

          if (data.data.estimated_win_rate !== undefined) {
            estimatedWinRate = data.data.estimated_win_rate;
          }

          if (data.data.estimated_return !== undefined) {
            estimatedReturn = data.data.estimated_return;
          }

          setStats({
            signalCount: detectedSignals.length,
            buySignals: buyCount,
            sellSignals: sellCount,
            estimatedWinRate,
            estimatedReturn,
          });

          // Set portfolio simulation if available
          if (data.data.portfolio_simulation) {
            setPortfolioSimulation(data.data.portfolio_simulation);
          } else {
            setPortfolioSimulation(null);
          }
        } else {
          setSignals([]);
          setStats(null);
          setPortfolioSimulation(null);
        }
      } catch (err) {
        console.error('Failed to simulate signals:', err);
        setSignals([]);
        setStats(null);
        setPortfolioSimulation(null);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    signals,
    stats,
    portfolioSimulation,
    loading,
    runSimulation,
  };
}
