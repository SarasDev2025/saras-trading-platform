import { Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useTradingMode } from "@/contexts/TradingModeContext";

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { tradingMode } = useTradingMode();

  // Determine badge styling based on trading mode
  const isLive = tradingMode === 'live';
  const badgeColor = isLive ? 'bg-[var(--warning-yellow)]' : 'bg-[var(--success-green)]';
  const badgeBgColor = isLive ? 'bg-[var(--warning-yellow)]' : 'bg-[var(--success-green)]';
  const badgeText = isLive ? 'warning-text' : 'success-text';
  const modeName = isLive ? 'LIVE' : 'PAPER';

  return (
    <header className="bg-[var(--carbon-gray-90)] border-b border-[var(--carbon-gray-80)] px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">{title}</h1>
          {subtitle && (
            <p className="text-gray-400 text-sm">{subtitle}</p>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <ThemeToggle />
          <Button
            variant="outline"
            size="icon"
            className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] hover:bg-[var(--carbon-gray-70)] text-white relative"
            title="Notifications"
          >
            <Bell className="h-[1.2rem] w-[1.2rem]" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-[var(--danger-red)] rounded-full"></span>
          </Button>
          <div className={`flex items-center space-x-2 px-3 py-1 ${badgeBgColor} bg-opacity-20 rounded-full`}>
            <div className={`w-2 h-2 ${badgeColor} rounded-full ${isLive ? '' : 'animate-pulse'}`}></div>
            <span className={`text-sm font-semibold ${badgeText}`}>{modeName}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
