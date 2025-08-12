import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { PortfolioOverview } from "@/components/dashboard/portfolio-overview";
import { PortfolioChart } from "@/components/dashboard/portfolio-chart";
import { AssetAllocation } from "@/components/dashboard/asset-allocation";
import { RecentTrades } from "@/components/dashboard/recent-trades";
import { QuickTradeModal } from "@/components/trading/quick-trade-modal";
import { Button } from "@/components/ui/button";
import { Plus, Scale } from "lucide-react";
import { useState } from "react";

export default function Dashboard() {
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      
      <main className="flex-1 overflow-hidden">
        <Header 
          title="Dashboard" 
          subtitle="Welcome back, manage your portfolio and trading activities"
        />
        
        <div className="p-6 h-full overflow-y-auto">
          <PortfolioOverview />
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            <div className="lg:col-span-2">
              <PortfolioChart />
            </div>
            <div className="lg:col-span-1">
              <AssetAllocation />
            </div>
          </div>
          
          <RecentTrades />
        </div>
      </main>

      {/* Quick Actions */}
      <div className="fixed bottom-6 right-6 flex flex-col space-y-4">
        <Button
          onClick={() => setIsTradeModalOpen(true)}
          size="icon"
          className="w-14 h-14 btn-primary rounded-full shadow-lg"
          title="Quick Trade"
        >
          <Plus className="h-6 w-6" />
        </Button>
        <Button
          size="icon"
          className="w-14 h-14 btn-success rounded-full shadow-lg"
          title="Rebalance Portfolio"
        >
          <Scale className="h-6 w-6" />
        </Button>
      </div>

      <QuickTradeModal 
        isOpen={isTradeModalOpen}
        onClose={() => setIsTradeModalOpen(false)}
      />
    </div>
  );
}
