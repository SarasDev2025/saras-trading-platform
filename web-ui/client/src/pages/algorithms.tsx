import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Play, Pause, Code, TrendingUp } from "lucide-react";

export default function Algorithms() {
  const mockAlgorithms = [
    {
      id: "1",
      name: "RSI Signals",
      description: "Generate buy/sell signals based on RSI indicator",
      language: "python",
      isActive: true,
      lastRun: "2024-01-15T10:30:00Z",
      performance: { accuracy: 0.73, trades: 45, pnl: 12450 },
    },
    {
      id: "2",
      name: "Moving Average Crossover",
      description: "SMA crossover strategy with dynamic parameters",
      language: "python",
      isActive: false,
      lastRun: null,
      performance: { accuracy: 0.68, trades: 32, pnl: 8200 },
    },
    {
      id: "3",
      name: "Bollinger Band Squeeze",
      description: "Identify volatility contractions and expansions",
      language: "python",
      isActive: true,
      lastRun: "2024-01-15T09:15:00Z",
      performance: { accuracy: 0.71, trades: 28, pnl: 9850 },
    },
  ];

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      
      <main className="flex-1 overflow-hidden">
        <Header 
          title="Algorithms" 
          subtitle="Manage and monitor your trading algorithms"
        />
        
        <div className="p-6 h-full overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Your Algorithms</h2>
            <div className="space-x-2">
              <Button variant="outline" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                Import
              </Button>
              <Button className="btn-primary">
                <Code className="w-4 h-4 mr-2" />
                New Algorithm
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
            {mockAlgorithms.map((algorithm) => (
              <Card key={algorithm.id} className="chart-container">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-white text-lg">{algorithm.name}</CardTitle>
                    <Switch checked={algorithm.isActive} />
                  </div>
                  <p className="text-sm text-gray-400 mt-2">{algorithm.description}</p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-400">Language</span>
                      <Badge variant="secondary" className="bg-[var(--carbon-gray-80)] text-white">
                        {algorithm.language.toUpperCase()}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-400">Status</span>
                      <Badge 
                        className={
                          algorithm.isActive 
                            ? "bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]"
                            : "bg-[var(--carbon-gray-80)] text-gray-400"
                        }
                      >
                        {algorithm.isActive ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-400">Last Run</span>
                      <span className="text-sm text-white">
                        {formatDateTime(algorithm.lastRun)}
                      </span>
                    </div>

                    <div className="border-t border-[var(--carbon-gray-80)] pt-4">
                      <h4 className="text-sm font-medium text-gray-400 mb-3">Performance</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400">Accuracy</span>
                          <span className="text-xs text-white font-medium">
                            {(algorithm.performance.accuracy * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400">Trades</span>
                          <span className="text-xs text-white font-medium">
                            {algorithm.performance.trades}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400">P&L</span>
                          <span className={`text-xs font-medium ${
                            algorithm.performance.pnl >= 0 ? 'success-text' : 'danger-text'
                          }`}>
                            ${algorithm.performance.pnl.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex space-x-2 pt-4">
                      <Button 
                        size="sm" 
                        className="flex-1 btn-primary"
                        disabled={!algorithm.isActive}
                      >
                        {algorithm.isActive ? (
                          <>
                            <Play className="w-3 h-3 mr-1" />
                            Run
                          </>
                        ) : (
                          <>
                            <Pause className="w-3 h-3 mr-1" />
                            Paused
                          </>
                        )}
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]"
                      >
                        Edit
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Algorithm Performance Overview */}
          <Card className="chart-container">
            <CardHeader>
              <CardTitle className="text-white flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                Algorithm Performance Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold success-text">3</div>
                  <div className="text-sm text-gray-400">Active Algorithms</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">105</div>
                  <div className="text-sm text-gray-400">Total Trades</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold success-text">71.2%</div>
                  <div className="text-sm text-gray-400">Avg Accuracy</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold success-text">$30,500</div>
                  <div className="text-sm text-gray-400">Total P&L</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
