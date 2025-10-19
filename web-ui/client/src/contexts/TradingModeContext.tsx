// =====================================================
// contexts/TradingModeContext.tsx - Trading Mode State Management
// =====================================================

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { apiRequest } from '@/lib/axios';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';

type TradingMode = 'paper' | 'live';

interface TradingModeContextType {
  tradingMode: TradingMode;
  isLoading: boolean;
  switchMode: (mode: TradingMode) => Promise<void>;
  isSwitching: boolean;
}

const TradingModeContext = createContext<TradingModeContextType | undefined>(undefined);

export const TradingModeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [tradingMode, setTradingMode] = useState<TradingMode>('paper');
  const [isLoading, setIsLoading] = useState(true);
  const [isSwitching, setIsSwitching] = useState(false);

  // Initialize trading mode from user data
  useEffect(() => {
    if (user?.trading_mode) {
      setTradingMode(user.trading_mode as TradingMode);
      setIsLoading(false);
    } else {
      // Default to paper if user data not available yet
      setTradingMode('paper');
      setIsLoading(false);
    }
  }, [user]);

  const switchMode = useCallback(async (mode: TradingMode) => {
    if (mode === tradingMode) {
      return; // Already in this mode
    }

    setIsSwitching(true);

    try {
      // Call API to update trading mode
      const response = await apiRequest.patch('/api/v1/settings/trading-mode', {
        trading_mode: mode
      });

      if (response.data.success) {
        setTradingMode(mode);

        // Invalidate all queries to refetch with new mode
        queryClient.invalidateQueries({ queryKey: ['/api/portfolios'] });
        queryClient.invalidateQueries({ queryKey: ['portfolios', 'cash-balance'] });
        queryClient.invalidateQueries({ queryKey: ['/api/smallcases'] });
        queryClient.invalidateQueries({ queryKey: ['/api/trades'] });

        // Show success message
        const modeName = mode === 'paper' ? 'Paper Trading' : 'Live Trading';
        toast({
          title: "Trading Mode Switched",
          description: `Switched to ${modeName} mode successfully.`,
          variant: mode === 'live' ? 'default' : 'default',
        });
      } else {
        throw new Error(response.data.message || 'Failed to switch trading mode');
      }
    } catch (error: any) {
      console.error('Error switching trading mode:', error);
      toast({
        title: "Failed to Switch Mode",
        description: error.response?.data?.detail || error.message || 'An error occurred while switching trading mode',
        variant: "destructive",
      });
      throw error;
    } finally {
      setIsSwitching(false);
    }
  }, [tradingMode, queryClient, toast]);

  return (
    <TradingModeContext.Provider
      value={{
        tradingMode,
        isLoading,
        switchMode,
        isSwitching
      }}
    >
      {children}
    </TradingModeContext.Provider>
  );
};

export const useTradingMode = () => {
  const context = useContext(TradingModeContext);
  if (context === undefined) {
    throw new Error('useTradingMode must be used within a TradingModeProvider');
  }
  return context;
};
