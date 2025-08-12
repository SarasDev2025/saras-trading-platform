import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const mockAllocationData = [
  { name: 'Equities', value: 67.3, color: 'var(--carbon-blue)' },
  { name: 'Fixed Income', value: 18.7, color: 'var(--success-green)' },
  { name: 'Commodities', value: 7.5, color: 'var(--warning-yellow)' },
  { name: 'Cash', value: 6.5, color: 'var(--carbon-gray-70)' },
];

export function AssetAllocation() {
  return (
    <Card className="chart-container">
      <CardHeader className="border-b border-[var(--carbon-gray-80)]">
        <CardTitle className="text-lg font-semibold text-white">
          Asset Allocation
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="h-64 mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={mockAllocationData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {mockAllocationData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-3">
          {mockAllocationData.map((asset, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: asset.color }}
                ></div>
                <span className="text-sm text-white">{asset.name}</span>
              </div>
              <span className="text-sm font-medium text-white">{asset.value}%</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
