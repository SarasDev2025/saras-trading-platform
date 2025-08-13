import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import { api } from "./api";
import type {
  Trade, AllocationItem, AlpacaAccount, PlatformInfo, PortfolioStatusItem
} from "./types";

/** Trades */
export const useTrades = (
  portfolioId: string,
  enabled = true,
  options?: UseQueryOptions<Trade[]>
) =>
  useQuery<Trade[]>({
    queryKey: ["trades", portfolioId],
    queryFn: async () => (await api.get(`/portfolio/${portfolioId}/trades`)).data,
    enabled,
    ...options,
  });

/** Asset allocation */
export const useAllocation = (
  portfolioId: string,
  options?: UseQueryOptions<AllocationItem[]>
) =>
  useQuery<AllocationItem[]>({
    queryKey: ["allocation", portfolioId],
    queryFn: async () => (await api.get(`/portfolio/${portfolioId}/allocation`)).data,
    ...options,
  });

/** Alpaca account */
export const useAlpacaAccount = (options?: UseQueryOptions<AlpacaAccount>) =>
  useQuery<AlpacaAccount>({
    queryKey: ["alpaca", "account"],
    queryFn: async () => (await api.get(`/alpaca/account`)).data,
    ...options,
  });

/** Platform info */
export const usePlatformInfo = (options?: UseQueryOptions<PlatformInfo>) =>
  useQuery<PlatformInfo>({
    queryKey: ["platform", "info"],
    queryFn: async () => (await api.get(`/platform/info`)).data,
    ...options,
  });

/** Portfolio status */
export const usePortfolioStatus = (
  options?: UseQueryOptions<PortfolioStatusItem[]>
) =>
  useQuery<PortfolioStatusItem[]>({
    queryKey: ["portfolio", "status"],
    queryFn: async () => (await api.get(`/portfolio/status`)).data,
    ...options,
  });
