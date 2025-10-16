import { useState, useCallback } from 'react';

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

export function useChartData() {
  const [priceData, setPriceData] = useState<PriceDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (symbol: string, timeRange: string) => {
    setLoading(true);
    setError(null);

    try {
      // Map time ranges to days
      const daysMap: Record<string, number> = {
        '1M': 30,
        '3M': 90,
        '6M': 180,
        '1Y': 365,
      };

      const days = daysMap[timeRange] || 90;

      const response = await fetch(
        `/api/v1/algorithms/visual/preview-data?symbol=${symbol}&days=${days}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      const data = await response.json();

      if (data.success) {
        setPriceData(data.data.price_data);
      } else {
        setError(data.message || 'Failed to fetch chart data');
        setPriceData([]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch chart data');
      setPriceData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    priceData,
    loading,
    error,
    fetchData,
  };
}
