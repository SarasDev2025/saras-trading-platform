import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { portfolioAPI } from '../lib/api';

// Portfolio management hooks
export const usePortfolios = () => {
  return useQuery({
    queryKey: ['portfolios'],
    queryFn: () => portfolioAPI.getPortfolios(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const usePortfolio = (portfolioId: string, enabled = true) => {
  return useQuery({
    queryKey: ['portfolio', portfolioId],
    queryFn: () => portfolioAPI.getPortfolio(portfolioId),
    enabled: enabled && !!portfolioId,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
};

export const useCreatePortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: portfolioAPI.createPortfolio,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });
};

export const useUpdatePortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ portfolioId, updates }: { 
      portfolioId: string; 
      updates: { name?: string; description?: string; } 
    }) => portfolioAPI.updatePortfolio(portfolioId, updates),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', variables.portfolioId] });
    },
  });
};

export const useDeletePortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: portfolioAPI.deletePortfolio,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    },
  });
};
