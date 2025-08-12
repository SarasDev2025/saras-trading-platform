import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { Target, TrendingUp, Settings } from "lucide-react";

export default function Strategies() {
  const mockStrategies = [
    {
      id: "1",
      name: "Momentum Strategy",
      description: "Buy high momentum stocks with strong technical indicators",
      type: "MOMENTUM",
      isActive: true,
      allocation: 35,
      performance: { return: 12.5, sharpe: 1.8, maxDrawdown: 8.2 },
      positions: 15,
    },
    {
      id: "2",
      name: "Mean Reversion",
      description: "Buy oversold stocks that are likely to bounce back",
      type: "MEAN_REVERSION",
      isActive: false,
      allocation: 25,
      performance: { return: 8.3, sharpe: 1.2, maxDrawdown: 12.1 },
      positions: 12,
    },
    {
      id: "3",
      name: "Value Investing",
      description: "Long-term value picks based on fundamental analysis",
      type: "VALUE",
      isActive: true,
      allocation: 40,
      performance: { return: 15.7, sharpe: 2.1, maxDrawdown: 6.8 },
      positions: 8,
    },
  ];

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      
      <main className="flex-1 overflow-hidden">
        <Header 
          title="Strategies" 
          subtitle="Manage and monitor your investment strategies"
        />
        
        <div className="p-6 h-full overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Your Strategies</h2>
            <div className="space-x-2">
              <Button variant="outline" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                Rebalance All
              </Button>
              <Button className="btn-primary">
                <Target className="w-4 h-4 mr-2" />
                New Strategy
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
            {mockStrategies.map((strategy) => (
              <Card key={strategy.id} className="chart-container">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-white text-lg">{strategy.name}</CardTitle>
                    <Switch checked={strategy.isActive} />
                  </div>
                  <p className="text-sm text-gray-400 mt-2">{strategy.description}</p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-400">Type</span>
                      <Badge variant="secondary" className="bg-[var(--carbon-gray-80)] text-white">
                        {strategy.type.replace('_', ' ')}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-400">Status</span>
                      <Badge 
                        className={
                          strategy.isActive 
                            ? "bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]"
                            : "bg-[var(--carbon-gray-80)] text-gray-400"
                        }
                      >
                        {strategy.isActive ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Allocation</span>
                        <span className="text-sm text-white font-medium">{strategy.allocation}%</span>
                      </div>
                      <Progress value={strategy.allocation} className="h-2" />
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-400">Positions</span>
                      <span className="text-sm text-white">{strategy.positions}</span>
                    </div>

                    <div className="border-t border-[var(--carbon-gray-80)] pt-4">
                      <h4 className="text-sm font-medium text-gray-400 mb-3">Performance</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400">Return</span>
                          <span className="text-xs success-text font-medium">
                            +{strategy.performance.return}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400">Sharpe Ratio</span>
                          <span className="text-xs text-white font-medium">
                            {strategy.performance.sharpe}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-400">Max Drawdown</span>
                          <span className="text-xs danger-text font-medium">
                            -{strategy.performance.maxDrawdown}%
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex space-x-2 pt-4">
                      <Button 
                        size="sm" 
                        className="flex-1 btn-primary"
                        disabled={!strategy.isActive}
                      >
                        Rebalance
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]"
                      >
                        <Settings className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Strategy Performance Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Card className="chart-container">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Strategy Allocation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockStrategies.map((strategy) => (
                    <div key={strategy.id}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-white">{strategy.name}</span>
                        <span className="text-sm text-gray-400">{strategy.allocation}%</span>
                      </div>
                      <Progress value={strategy.allocation} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="chart-container">
              <CardHeader>
                <CardTitle className="text-white">Performance Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold success-text">+12.2%</div>
                    <div className="text-sm text-gray-400">Average Return</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">1.7</div>
                    <div className="text-sm text-gray-400">Average Sharpe</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">35</div>
                    <div className="text-sm text-gray-400">Total Positions</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold danger-text">-9.0%</div>
                    <div className="text-sm text-gray-400">Max Drawdown</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
