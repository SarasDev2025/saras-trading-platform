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

export function useSignalSimulation() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [stats, setStats] = useState<SignalStats | null>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = useCallback(
    async (
      priceData: PriceDataPoint[],
      entryConditions: Condition[],
      exitConditions: Condition[]
    ) => {
      if (priceData.length === 0) {
        setSignals([]);
        setStats(null);
        return;
      }

      setLoading(true);

      try {
        const response = await fetch('/api/v1/algorithms/visual/preview-signals', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            price_data: priceData,
            entry_conditions: entryConditions,
            exit_conditions: exitConditions,
          }),
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
        } else {
          setSignals([]);
          setStats(null);
        }
      } catch (err) {
        console.error('Failed to simulate signals:', err);
        setSignals([]);
        setStats(null);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    signals,
    stats,
    loading,
    runSimulation,
  };
}
