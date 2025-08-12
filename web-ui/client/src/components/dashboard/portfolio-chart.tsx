import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';
import { useState } from "react";

const mockChartData = [
  { time: '9:30', value: 2800000 },
  { time: '10:00', value: 2810000 },
  { time: '10:30', value: 2795000 },
  { time: '11:00', value: 2820000 },
  { time: '11:30', value: 2835000 },
  { time: '12:00', value: 2845000 },
  { time: '12:30', value: 2830000 },
  { time: '13:00', value: 2850000 },
  { time: '13:30', value: 2847392 },
  { time: '14:00', value: 2852000 },
  { time: '14:30', value: 2843000 },
  { time: '15:00', value: 2851000 },
  { time: '15:30', value: 2847392 },
  { time: '16:00', value: 2847392 },
];

export function PortfolioChart() {
  const [timeframe, setTimeframe] = useState("1D");

  return (
    <Card className="chart-container">
      <CardHeader className="border-b border-[var(--carbon-gray-80)]">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-white">
            Portfolio Performance
          </CardTitle>
          <Select value={timeframe} onValueChange={setTimeframe}>
            <SelectTrigger className="w-20 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
              <SelectItem value="1D" className="text-white hover:bg-[var(--carbon-gray-70)]">1D</SelectItem>
              <SelectItem value="1W" className="text-white hover:bg-[var(--carbon-gray-70)]">1W</SelectItem>
              <SelectItem value="1M" className="text-white hover:bg-[var(--carbon-gray-70)]">1M</SelectItem>
              <SelectItem value="3M" className="text-white hover:bg-[var(--carbon-gray-70)]">3M</SelectItem>
              <SelectItem value="1Y" className="text-white hover:bg-[var(--carbon-gray-70)]">1Y</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--carbon-gray-70)" />
              <XAxis 
                dataKey="time" 
                tick={{ fill: '#a1a1aa', fontSize: 12 }}
                axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                tickLine={{ stroke: 'var(--carbon-gray-70)' }}
              />
              <YAxis 
                tick={{ fill: '#a1a1aa', fontSize: 12 }}
                axisLine={{ stroke: 'var(--carbon-gray-70)' }}
                tickLine={{ stroke: 'var(--carbon-gray-70)' }}
                tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="var(--carbon-blue)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: 'var(--carbon-blue)' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
