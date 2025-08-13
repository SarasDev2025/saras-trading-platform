import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import type { Trade } from "@shared/schema";
import { Skeleton } from "@/components/ui/skeleton";
import { useState } from "react";
import { api } from "@/lib/api"; // <-- new

const tabs = [
  { id: "trades", label: "Recent Trades" },
  { id: "positions", label: "Top Positions" },
  { id: "strategies", label: "Active Strategies" },
  { id: "algorithms", label: "Algorithms" },
];

type Trade = {
  id: number;
  createdAt: string;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  price: number;
  value: number;
  status: "FILLED" | "PENDING" | "CANCELLED";
};

export function RecentTrades() {
  const [activeTab, setActiveTab] = useState("trades");
  const portfolioId = "portfolio-id"; // later: pass as prop or read from route

  const { data: trades = [], isLoading, isError, error } = useQuery<Trade[]>({
    queryKey: ["/portfolio", portfolioId, "trades"],
    enabled: activeTab === "trades",
    queryFn: async () => {
      const res = await api.get(`/trade/portfolios/${portfolioId}/trades`);
      console.log("[RQ] queryFn done", res.status, res.request?.responseURL);
  
      if (!Array.isArray(res.data)) {
        throw new Error("Trades API did not return an array");
      }
      return res.data; // ✅ always an array now
    },
  });
  
const formatTime = (date: string) =>
    new Date(date).toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });

  const formatCurrency = (value: string) =>
    parseFloat(value).toLocaleString("en-US", { style: "currency", currency: "USD" });

  return (
    <Card className="chart-container">
      <div className="border-b border-[var(--carbon-gray-80)]">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-[var(--carbon-blue)] carbon-blue'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <CardContent className="p-6">
        {activeTab === "trades" && (
          <>
            {isError && (
              <p className="text-red-400 mb-3">Failed to load trades: {(error as Error)?.message}</p>
            )}

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left border-b border-[var(--carbon-gray-80)]">
                    <th className="pb-3 text-sm font-medium text-gray-400">Time</th>
                    <th className="pb-3 text-sm font-medium text-gray-400">Symbol</th>
                    <th className="pb-3 text-sm font-medium text-gray-400">Side</th>
                    <th className="pb-3 text-sm font-medium text-gray-400">Quantity</th>
                    <th className="pb-3 text-sm font-medium text-gray-400">Price</th>
                    <th className="pb-3 text-sm font-medium text-gray-400">Value</th>
                    <th className="pb-3 text-sm font-medium text-gray-400">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <tr key={i} className="border-b border-[var(--carbon-gray-80)]">
                        <td className="py-3"><Skeleton className="h-4 w-16" /></td>
                        <td className="py-3"><Skeleton className="h-4 w-12" /></td>
                        <td className="py-3"><Skeleton className="h-6 w-12" /></td>
                        <td className="py-3"><Skeleton className="h-4 w-16" /></td>
                        <td className="py-3"><Skeleton className="h-4 w-16" /></td>
                        <td className="py-3"><Skeleton className="h-4 w-20" /></td>
                        <td className="py-3"><Skeleton className="h-6 w-16" /></td>
                      </tr>
                    ))
                  ) : (
                    trades.map((trade) => (
                      <tr key={trade.id} className="border-b border-[var(--carbon-gray-80)]">
                        <td className="py-3 text-sm text-white">
                          {trade.createdAt ? formatTime(trade.createdAt.toString()) : "N/A"}
                        </td>
                        <td className="py-3 text-sm font-medium text-white">{trade.symbol}</td>
                        <td className="py-3">
                          <Badge 
                            variant={trade.side === "BUY" ? "default" : "destructive"}
                            className={
                              trade.side === "BUY"
                                ? "bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]"
                                : "bg-[var(--danger-red)] bg-opacity-20 text-[var(--danger-red)]"
                            }
                          >
                            {trade.side}
                          </Badge>
                        </td>
                        <td className="py-3 text-sm text-white">{trade.quantity}</td>
                        <td className="py-3 text-sm text-white">{formatCurrency(trade.price.toString())}</td>
                        <td className="py-3 text-sm text-white">{formatCurrency(trade.value.toString())}</td>
                        <td className="py-3">
                          <Badge
                            variant={trade.status === "FILLED" ? "default" : "secondary"}
                            className={
                              trade.status === "FILLED"
                                ? "bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]"
                                : trade.status === "PENDING"
                                ? "bg-[var(--warning-yellow)] bg-opacity-20 text-[var(--warning-yellow)]"
                                : "bg-[var(--danger-red)] bg-opacity-20 text-[var(--danger-red)]"
                            }
                          >
                            {trade.status}
                          </Badge>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between mt-6">
              <p className="text-sm text-gray-400">
                Showing {trades?.length || 0} of {trades?.length || 0} trades
              </p>
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">Previous</Button>
                <Button size="sm" className="btn-primary">1</Button>
                <Button variant="outline" size="sm" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">2</Button>
                <Button variant="outline" size="sm" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">Next</Button>
              </div>
            </div>
          </>
        )}

        {activeTab !== "trades" && (
          <div className="text-center py-8">
            <p className="text-gray-400">Content for {tabs.find(t => t.id === activeTab)?.label} coming soon</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
