import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Target, AlertTriangle, Activity } from "lucide-react";
import { useState } from "react";

const performanceData = [
  { date: '2024-01-01', portfolio: 2500000, benchmark: 2500000 },
  { date: '2024-01-15', portfolio: 2580000, benchmark: 2540000 },
  { date: '2024-02-01', portfolio: 2620000, benchmark: 2570000 },
  { date: '2024-02-15', portfolio: 2590000, benchmark: 2580000 },
  { date: '2024-03-01', portfolio: 2680000, benchmark: 2610000 },
  { date: '2024-03-15', portfolio: 2720000, benchmark: 2640000 },
  { date: '2024-04-01', portfolio: 2780000, benchmark: 2680000 },
  { date: '2024-04-15', portfolio: 2847392, benchmark: 2720000 },
];

const sectorData = [
  { sector: 'Technology', allocation: 35, performance: 12.5, color: 'var(--carbon-blue)' },
  { sector: 'Healthcare', allocation: 20, performance: 8.3, color: 'var(--success-green)' },
  { sector: 'Finance', allocation: 18, performance: 15.2, color: 'var(--warning-yellow)' },
  { sector: 'Consumer', allocation: 15, performance: 6.8, color: '#8B5CF6' },
  { sector: 'Industrial', allocation: 12, performance: 9.1, color: '#F97316' },
];

const riskMetrics = [
  { metric: 'Value at Risk (95%)', value: '$142,370', change: -2.1 },
  { metric: 'Beta', value: '1.18', change: 0.05 },
  { metric: 'Sharpe Ratio', value: '1.73', change: 0.12 },
  { metric: 'Max Drawdown', value: '8.4%', change: -1.2 },
];

const volumeData = [
  { date: '2024-04-08', volume: 1200000 },
  { date: '2024-04-09', volume: 950000 },
  { date: '2024-04-10', volume: 1800000 },
  { date: '2024-04-11', volume: 1350000 },
  { date: '2024-04-12', volume: 2100000 },
  { date: '2024-04-15', volume: 1750000 },
];

export default function Analytics() {
  const [timeframe, setTimeframe] = useState("3M");
  const [activeTab, setActiveTab] = useState("performance");

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      
      <main className="flex-1 overflow-hidden">
        <Header 
          title="Analytics" 
          subtitle="Comprehensive portfolio and trading analytics"
        />
        
        <div className="p-6 h-full overflow-y-auto">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-400">Total Return</h3>
                  <TrendingUp className="w-4 h-4 success-text" />
                </div>
                <div className="text-2xl font-bold success-text">+13.9%</div>
                <div className="text-sm text-gray-400 mt-2">vs 8.8% benchmark</div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-400">Alpha</h3>
                  <Target className="w-4 h-4 carbon-blue" />
                </div>
                <div className="text-2xl font-bold text-white">5.1%</div>
                <div className="text-sm success-text mt-2">Outperforming</div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-400">Volatility</h3>
                  <Activity className="w-4 h-4 warning-text" />
                </div>
                <div className="text-2xl font-bold text-white">16.2%</div>
                <div className="text-sm text-gray-400 mt-2">Annualized</div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-400">Risk Score</h3>
                  <AlertTriangle className="w-4 h-4 warning-text" />
                </div>
                <div className="text-2xl font-bold warning-text">Medium</div>
                <div className="text-sm text-gray-400 mt-2">7.2/10</div>
              </CardContent>
            </Card>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-4 bg-[var(--carbon-gray-90)] mb-6">
              <TabsTrigger value="performance" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                Performance
              </TabsTrigger>
              <TabsTrigger value="risk" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                Risk Analysis
              </TabsTrigger>
              <TabsTrigger value="sector" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                Sector Analysis
              </TabsTrigger>
              <TabsTrigger value="trading" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                Trading Activity
              </TabsTrigger>
            </TabsList>

            <TabsContent value="performance">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
                <div className="lg:col-span-2">
                  <Card className="chart-container">
                    <CardHeader className="border-b border-[var(--carbon-gray-80)]">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-white">Portfolio vs Benchmark</CardTitle>
                        <Select value={timeframe} onValueChange={setTimeframe}>
                          <SelectTrigger className="w-20 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                            <SelectItem value="1M" className="text-white">1M</SelectItem>
                            <SelectItem value="3M" className="text-white">3M</SelectItem>
                            <SelectItem value="6M" className="text-white">6M</SelectItem>
                            <SelectItem value="1Y" className="text-white">1Y</SelectItem>
                            <SelectItem value="ALL" className="text-white">ALL</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </CardHeader>
                    <CardContent className="p-6">
                      <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={performanceData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--carbon-gray-70)" />
                            <XAxis 
                              dataKey="date" 
                              tick={{ fill: '#a1a1aa', fontSize: 12 }}
                              axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                              tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            />
                            <YAxis 
                              tick={{ fill: '#a1a1aa', fontSize: 12 }}
                              axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                              tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
                            />
                            <Line 
                              type="monotone" 
                              dataKey="portfolio" 
                              stroke="var(--carbon-blue)"
                              strokeWidth={3}
                              dot={false}
                              name="Portfolio"
                            />
                            <Line 
                              type="monotone" 
                              dataKey="benchmark" 
                              stroke="var(--carbon-gray-70)"
                              strokeWidth={2}
                              strokeDasharray="5 5"
                              dot={false}
                              name="Benchmark"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div className="lg:col-span-1">
                  <Card className="chart-container h-fit">
                    <CardHeader>
                      <CardTitle className="text-white">Key Metrics</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        <div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-400">Annual Return</span>
                            <span className="text-sm success-text font-medium">+13.9%</span>
                          </div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-400">Benchmark</span>
                            <span className="text-sm text-gray-400">+8.8%</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Excess Return</span>
                            <span className="text-sm success-text font-medium">+5.1%</span>
                          </div>
                        </div>
                        
                        <div className="border-t border-[var(--carbon-gray-80)] pt-4">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-400">Best Month</span>
                            <span className="text-sm success-text">+8.2%</span>
                          </div>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-400">Worst Month</span>
                            <span className="text-sm danger-text">-4.1%</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-400">Win Rate</span>
                            <span className="text-sm text-white">68.4%</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="risk">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Risk Metrics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {riskMetrics.map((item, index) => (
                        <div key={index} className="flex items-center justify-between p-4 border border-[var(--carbon-gray-80)] rounded-lg">
                          <div>
                            <span className="text-white font-medium">{item.metric}</span>
                            <div className="text-2xl font-bold text-white mt-1">{item.value}</div>
                          </div>
                          <div className={`flex items-center ${item.change >= 0 ? 'success-text' : 'danger-text'}`}>
                            {item.change >= 0 ? (
                              <TrendingUp className="w-4 h-4 mr-1" />
                            ) : (
                              <TrendingDown className="w-4 h-4 mr-1" />
                            )}
                            <span className="text-sm font-medium">
                              {Math.abs(item.change)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Drawdown Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={performanceData.map((item, i) => ({ 
                          ...item, 
                          drawdown: Math.random() * -10 
                        }))}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--carbon-gray-70)" />
                          <XAxis 
                            dataKey="date" 
                            tick={{ fill: '#a1a1aa', fontSize: 12 }}
                            axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short' })}
                          />
                          <YAxis 
                            tick={{ fill: '#a1a1aa', fontSize: 12 }}
                            axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                            tickFormatter={(value) => `${value}%`}
                          />
                          <Area
                            type="monotone"
                            dataKey="drawdown"
                            stroke="var(--danger-red)"
                            fill="var(--danger-red)"
                            fillOpacity={0.3}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="sector">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Sector Allocation</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64 mb-6">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={sectorData}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            dataKey="allocation"
                          >
                            {sectorData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-3">
                      {sectorData.map((sector, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: sector.color }}
                            ></div>
                            <span className="text-sm text-white">{sector.sector}</span>
                          </div>
                          <span className="text-sm font-medium text-white">{sector.allocation}%</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Sector Performance</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={sectorData} layout="horizontal">
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--carbon-gray-70)" />
                          <XAxis 
                            type="number"
                            tick={{ fill: '#a1a1aa', fontSize: 12 }}
                            axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                            tickFormatter={(value) => `${value}%`}
                          />
                          <YAxis 
                            type="category"
                            dataKey="sector"
                            tick={{ fill: '#a1a1aa', fontSize: 12 }}
                            axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                            width={80}
                          />
                          <Bar 
                            dataKey="performance" 
                            fill="var(--carbon-blue)"
                            radius={[0, 4, 4, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="trading">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Trading Volume</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={volumeData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--carbon-gray-70)" />
                          <XAxis 
                            dataKey="date"
                            tick={{ fill: '#a1a1aa', fontSize: 12 }}
                            axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          />
                          <YAxis 
                            tick={{ fill: '#a1a1aa', fontSize: 12 }}
                            axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                            tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
                          />
                          <Bar 
                            dataKey="volume" 
                            fill="var(--carbon-blue)"
                            radius={[4, 4, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Trading Statistics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-white">247</div>
                        <div className="text-sm text-gray-400">Total Trades</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold success-text">68.4%</div>
                        <div className="text-sm text-gray-400">Win Rate</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-white">$8.2M</div>
                        <div className="text-sm text-gray-400">Avg Daily Volume</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold success-text">2.3</div>
                        <div className="text-sm text-gray-400">Profit Factor</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
