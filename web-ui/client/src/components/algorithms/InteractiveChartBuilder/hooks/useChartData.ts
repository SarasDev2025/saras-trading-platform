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
  const [priceDataMap, setPriceDataMap] = useState<Record<string, PriceDataPoint[]>>({});
  const [compositeData, setCompositeData] = useState<Array<{ date: string; composite_index: number }>>([]);
  const [primarySymbol, setPrimarySymbol] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (symbols: string[], timeRange: string) => {
    setLoading(true);
    setError(null);

    try {
      if (!symbols || symbols.length === 0) {
        setPriceDataMap({});
        setCompositeData([]);
        setPrimarySymbol(null);
        setLoading(false);
        return;
      }

      // Map time ranges to days
      const daysMap: Record<string, number> = {
        '1M': 30,
        '3M': 90,
        '6M': 180,
        '1Y': 365,
      };

      const days = daysMap[timeRange] || 90;

      const symbolParam = symbols.join(',');

      const response = await fetch(
        `/api/v1/algorithms/visual/preview-data?symbols=${encodeURIComponent(symbolParam)}&days=${days}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      const data = await response.json();

      if (data.success) {
        setPriceDataMap(data.data.symbols || {});
        setCompositeData(data.data.composite || []);
        setPrimarySymbol(data.data.primary_symbol || symbols[0]);
      } else {
        setError(data.message || 'Failed to fetch chart data');
        setPriceDataMap({});
        setCompositeData([]);
        setPrimarySymbol(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch chart data');
      setPriceDataMap({});
      setCompositeData([]);
      setPrimarySymbol(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    priceDataMap,
    compositeData,
    primarySymbol,
    loading,
    error,
    fetchData,
  };
}
