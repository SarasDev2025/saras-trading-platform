import { Link, useLocation } from "wouter";
import {
  Home,
  Wallet,
  TrendingUp,
  Bot,
  Target,
  BarChart3,
  Settings,
  LogOut,
  Activity,
  Package
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";

const navigation = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Portfolio", href: "/portfolio", icon: Wallet },
  { name: "Trading", href: "/trading", icon: TrendingUp },
  { name: "Smallcases", href: "/smallcases", icon: Package },
  { name: "Algorithms", href: "/algorithms", icon: Bot },
  { name: "Strategies", href: "/strategies", icon: Target },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const [location, setLocation] = useLocation();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    setLocation('/auth/login');
  };

  const userInitials = user ?
    `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() :
    'U';
  const userName = user ?
    `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email :
    'User';

  return (
    <aside className="w-64 sidebar-nav flex-shrink-0 flex flex-col">
      <div className="p-6">
        <div className="flex items-center space-x-3 mb-8">
          <div className="w-8 h-8 bg-carbon-blue rounded flex items-center justify-center">
            <Activity className="text-white w-4 h-4" />
          </div>
          <h1 className="text-xl font-semibold text-white">TradePro</h1>
        </div>
        
        <nav className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location === item.href;
            
            return (
              <Link key={item.name} href={item.href}>
                <a
                  className={cn(
                    "flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors",
                    isActive ? "nav-item-active" : "nav-item"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </a>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto p-6 border-t border-[var(--carbon-gray-80)]">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-carbon-blue rounded-full flex items-center justify-center">
            <span className="text-white font-medium">{userInitials}</span>
          </div>
          <div className="flex-1">
            <p className="font-medium text-white">{userName}</p>
            <p className="text-sm text-gray-400">Trader</p>
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-white transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
