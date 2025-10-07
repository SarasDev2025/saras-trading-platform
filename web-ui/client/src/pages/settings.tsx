import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  User,
  Settings as SettingsIcon,
  Shield,
  Bell,
  Palette,
  Database,
  Key,
  AlertTriangle,
  Check,
  DollarSign,
  TrendingUp
} from "lucide-react";
import { useState, useMemo, useEffect } from "react";
import { useTheme } from "@/hooks/use-theme";
import { useTradingMode } from "@/contexts/TradingModeContext";
import { useAuth } from "@/hooks/useAuth";
import { useQuery } from "@tanstack/react-query";

export default function Settings() {
  const { theme, setTheme } = useTheme();
  const { tradingMode, switchMode, isSwitching } = useTradingMode();
  const { user } = useAuth();

  const [notifications, setNotifications] = useState({
    trades: true,
    priceAlerts: true,
    portfolio: false,
    news: true,
  });

  // Fetch broker configuration from database based on user's region and trading mode
  const { data: brokerConfig, isLoading: isBrokerLoading } = useQuery({
    queryKey: ["/api/v1/broker-config/current"],
    enabled: !!user, // Only fetch when user is loaded
  });

  const [tradingSettings, setTradingSettings] = useState({
    maxPositionSize: "10000",
    stopLossDefault: "5",
    takeProfitDefault: "10",
    riskPerTrade: "2",
  });

  // Admin user check (you may want to get this from auth context)
  const [isAdmin, setIsAdmin] = useState(false);

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      
      <main className="flex-1 overflow-hidden">
        <Header 
          title="Settings" 
          subtitle="Manage your account, trading preferences, and system settings"
        />
        
        <div className="p-6 h-full overflow-y-auto">
          <Tabs defaultValue="profile" className="w-full">
            <TabsList className={`grid w-full ${isAdmin ? 'grid-cols-7' : 'grid-cols-6'} bg-[var(--carbon-gray-90)] mb-6`}>
              <TabsTrigger value="profile" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                <User className="w-4 h-4 mr-2" />
                Profile
              </TabsTrigger>
              <TabsTrigger value="trading" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                <SettingsIcon className="w-4 h-4 mr-2" />
                Trading
              </TabsTrigger>
              <TabsTrigger value="security" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                <Shield className="w-4 h-4 mr-2" />
                Security
              </TabsTrigger>
              <TabsTrigger value="notifications" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                <Bell className="w-4 h-4 mr-2" />
                Alerts
              </TabsTrigger>
              <TabsTrigger value="appearance" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                <Palette className="w-4 h-4 mr-2" />
                Theme
              </TabsTrigger>
              <TabsTrigger value="api" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                <Key className="w-4 h-4 mr-2" />
                API
              </TabsTrigger>
              {isAdmin && (
                <TabsTrigger value="admin" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">
                  <Database className="w-4 h-4 mr-2" />
                  Admin
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="profile">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Personal Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Full Name</Label>
                      <Input
                        key={`name-${user?.id}`}
                        defaultValue={user ? `${user.first_name || ''} ${user.last_name || ''}`.trim() : ''}
                        placeholder="Enter your full name"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Email</Label>
                      <Input
                        key={`email-${user?.id}`}
                        defaultValue={user?.email || ''}
                        type="email"
                        placeholder="Enter your email"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Region</Label>
                      <Input
                        value={user?.region || 'IN'}
                        disabled
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-gray-400"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Role</Label>
                      <Select defaultValue="portfolio_manager">
                        <SelectTrigger className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                          <SelectItem value="trader" className="text-white">Trader</SelectItem>
                          <SelectItem value="portfolio_manager" className="text-white">Portfolio Manager</SelectItem>
                          <SelectItem value="analyst" className="text-white">Analyst</SelectItem>
                          <SelectItem value="admin" className="text-white">Administrator</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Phone</Label>
                      <Input
                        defaultValue="+1 (555) 123-4567"
                        type="tel"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                    <Button className="w-full btn-primary mt-6">
                      Update Profile
                    </Button>
                  </CardContent>
                </Card>

                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Developer Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-white font-medium">Admin Mode</span>
                        <div className="text-sm text-gray-400">Enable admin controls and configuration</div>
                      </div>
                      <Switch
                        checked={isAdmin}
                        onCheckedChange={setIsAdmin}
                      />
                    </div>
                    {isAdmin && (
                      <div className="p-3 bg-[var(--warning-yellow)] bg-opacity-10 border border-[var(--warning-yellow)] rounded-lg">
                        <div className="text-xs warning-text">
                          <strong>Admin Mode Enabled:</strong> You now have access to system configuration settings.
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Account Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between p-4 border border-[var(--carbon-gray-80)] rounded-lg">
                      <div>
                        <span className="text-white font-medium">Account Type</span>
                        <div className="text-sm text-gray-400 mt-1">Professional Trading</div>
                      </div>
                      <Badge className="bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]">
                        Active
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between p-4 border border-[var(--carbon-gray-80)] rounded-lg">
                      <div>
                        <span className="text-white font-medium">Verification</span>
                        <div className="text-sm text-gray-400 mt-1">KYC & AML Compliant</div>
                      </div>
                      <Check className="w-5 h-5 success-text" />
                    </div>
                    <div className="flex items-center justify-between p-4 border border-[var(--carbon-gray-80)] rounded-lg">
                      <div>
                        <span className="text-white font-medium">Trading Limits</span>
                        <div className="text-sm text-gray-400 mt-1">$10M daily limit</div>
                      </div>
                      <span className="text-sm success-text">Unlimited</span>
                    </div>
                    <div className="flex items-center justify-between p-4 border border-[var(--carbon-gray-80)] rounded-lg">
                      <div>
                        <span className="text-white font-medium">Member Since</span>
                        <div className="text-sm text-gray-400 mt-1">January 2022</div>
                      </div>
                      <span className="text-sm text-white">2+ years</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="trading">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Risk Management</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Max Position Size ($)</Label>
                      <Input
                        value={tradingSettings.maxPositionSize}
                        onChange={(e) => setTradingSettings({...tradingSettings, maxPositionSize: e.target.value})}
                        type="number"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Default Stop Loss (%)</Label>
                      <Input
                        value={tradingSettings.stopLossDefault}
                        onChange={(e) => setTradingSettings({...tradingSettings, stopLossDefault: e.target.value})}
                        type="number"
                        step="0.1"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Default Take Profit (%)</Label>
                      <Input
                        value={tradingSettings.takeProfitDefault}
                        onChange={(e) => setTradingSettings({...tradingSettings, takeProfitDefault: e.target.value})}
                        type="number"
                        step="0.1"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Risk Per Trade (%)</Label>
                      <Input
                        value={tradingSettings.riskPerTrade}
                        onChange={(e) => setTradingSettings({...tradingSettings, riskPerTrade: e.target.value})}
                        type="number"
                        step="0.1"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Trading Preferences</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <Label className="text-sm font-medium text-gray-400">Execution Mode</Label>
                      <Select
                        value={tradingMode}
                        onValueChange={(value: 'paper' | 'live') => switchMode(value)}
                        disabled={isSwitching}
                      >
                        <SelectTrigger className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                          <SelectItem value="paper" className="text-white">
                            <div className="flex items-center space-x-2">
                              <TrendingUp className="w-4 h-4 text-blue-400" />
                              <div>
                                <div className="font-medium">Paper Trading</div>
                                <div className="text-xs text-gray-400">Virtual money - Risk-free practice</div>
                              </div>
                            </div>
                          </SelectItem>
                          <SelectItem value="live" className="text-white">
                            <div className="flex items-center space-x-2">
                              <DollarSign className="w-4 h-4 text-green-400" />
                              <div>
                                <div className="font-medium">Live Trading</div>
                                <div className="text-xs text-gray-400">Real money - Actual profits & losses</div>
                              </div>
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                      {tradingMode === "live" && (
                        <div className="p-3 bg-[var(--warning-yellow)] bg-opacity-10 border border-[var(--warning-yellow)] rounded-lg">
                          <div className="flex items-center space-x-2">
                            <AlertTriangle className="w-4 h-4 warning-text flex-shrink-0" />
                            <div className="text-xs warning-text">
                              <strong>Live Trading:</strong> Real money at risk. Ensure sufficient funds in broker account.
                            </div>
                          </div>
                        </div>
                      )}
                      {isSwitching && (
                        <div className="text-xs text-gray-400 flex items-center space-x-2">
                          <span className="animate-pulse">Switching trading mode...</span>
                        </div>
                      )}
                    </div>
                    <Separator className="bg-[var(--carbon-gray-80)]" />

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm font-medium text-gray-400">Broker Configuration</Label>
                        <span className="text-xs text-gray-500">
                          Region: {user?.region || 'Loading...'} • Mode: {tradingMode}
                        </span>
                      </div>

                      {isBrokerLoading ? (
                        <div className="p-4 bg-[var(--carbon-gray-90)] border border-[var(--carbon-gray-80)] rounded-lg">
                          <div className="text-sm text-gray-400">Loading broker configuration...</div>
                        </div>
                      ) : brokerConfig ? (
                        <div className="p-4 bg-[var(--carbon-gray-90)] border border-[var(--carbon-gray-80)] rounded-lg space-y-3">
                          <div className="flex items-center space-x-3">
                            <div className={`w-3 h-3 rounded-full ${
                              brokerConfig.broker_name === 'zerodha' ? 'bg-orange-500' :
                              brokerConfig.broker_name === 'alpaca' ? 'bg-blue-500' :
                              'bg-purple-500'
                            }`}></div>
                            <div>
                              <div className="font-medium text-white">{brokerConfig.display_name}</div>
                              <div className="text-xs text-gray-400">{brokerConfig.description}</div>
                            </div>
                          </div>
                          <div className="pt-2 border-t border-[var(--carbon-gray-80)]">
                            <div className="text-xs text-gray-400 mb-1">API Endpoint:</div>
                            <div className="text-sm text-white font-mono break-all">{brokerConfig.api_url}</div>
                          </div>
                          <div className="text-xs text-gray-500 italic">
                            ✓ Auto-configured based on your region and trading mode
                          </div>
                        </div>
                      ) : (
                        <div className="p-4 bg-[var(--carbon-gray-90)] border border-[var(--carbon-gray-80)] rounded-lg">
                          <div className="text-sm text-gray-400">No broker configuration found</div>
                        </div>
                      )}
                    </div>
                    <Separator className="bg-[var(--carbon-gray-80)]" />

                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-white font-medium">Auto-execute algorithms</span>
                        <div className="text-sm text-gray-400">Allow algorithms to place trades automatically</div>
                      </div>
                      <Switch />
                    </div>
                    <Separator className="bg-[var(--carbon-gray-80)]" />
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-white font-medium">Pre-market trading</span>
                        <div className="text-sm text-gray-400">Enable trading before market open</div>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <Separator className="bg-[var(--carbon-gray-80)]" />
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-white font-medium">After-hours trading</span>
                        <div className="text-sm text-gray-400">Enable trading after market close</div>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <Separator className="bg-[var(--carbon-gray-80)]" />
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-white font-medium">Smart order routing</span>
                        <div className="text-sm text-gray-400">Optimize order execution across venues</div>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="security">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Authentication</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Current Password</Label>
                      <Input
                        type="password"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">New Password</Label>
                      <Input
                        type="password"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Confirm New Password</Label>
                      <Input
                        type="password"
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                    <Button className="w-full btn-primary">
                      Update Password
                    </Button>
                  </CardContent>
                </Card>

                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">Two-Factor Authentication</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between p-4 border border-[var(--success-green)] bg-[var(--success-green)] bg-opacity-10 rounded-lg">
                      <div>
                        <span className="text-white font-medium">2FA Status</span>
                        <div className="text-sm success-text mt-1">Enabled via Authenticator App</div>
                      </div>
                      <Check className="w-5 h-5 success-text" />
                    </div>
                    <div className="space-y-2">
                      <Button variant="outline" className="w-full bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                        View Recovery Codes
                      </Button>
                      <Button variant="outline" className="w-full bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                        Reconfigure 2FA
                      </Button>
                    </div>
                    
                    <Separator className="bg-[var(--carbon-gray-80)]" />
                    
                    <div>
                      <h4 className="text-white font-medium mb-3">Login Sessions</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between p-3 border border-[var(--carbon-gray-80)] rounded">
                          <div>
                            <span className="text-sm text-white">Current Session</span>
                            <div className="text-xs text-gray-400">Chrome • New York, NY</div>
                          </div>
                          <Badge className="bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]">
                            Active
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between p-3 border border-[var(--carbon-gray-80)] rounded">
                          <div>
                            <span className="text-sm text-white">Mobile App</span>
                            <div className="text-xs text-gray-400">iPhone • 2 hours ago</div>
                          </div>
                          <Button size="sm" variant="outline" className="text-xs bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                            Revoke
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="notifications">
              <Card className="chart-container">
                <CardHeader>
                  <CardTitle className="text-white">Notification Preferences</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <h3 className="text-lg font-medium text-white">Trading Alerts</h3>
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-white font-medium">Trade Executions</span>
                          <div className="text-sm text-gray-400">Get notified when trades are filled</div>
                        </div>
                        <Switch 
                          checked={notifications.trades}
                          onCheckedChange={(checked) => setNotifications({...notifications, trades: checked})}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-white font-medium">Price Alerts</span>
                          <div className="text-sm text-gray-400">Alerts for watchlist price targets</div>
                        </div>
                        <Switch 
                          checked={notifications.priceAlerts}
                          onCheckedChange={(checked) => setNotifications({...notifications, priceAlerts: checked})}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-white font-medium">Portfolio Updates</span>
                          <div className="text-sm text-gray-400">Daily portfolio performance summary</div>
                        </div>
                        <Switch 
                          checked={notifications.portfolio}
                          onCheckedChange={(checked) => setNotifications({...notifications, portfolio: checked})}
                        />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h3 className="text-lg font-medium text-white">Market News</h3>
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-white font-medium">Breaking News</span>
                          <div className="text-sm text-gray-400">Important market-moving news</div>
                        </div>
                        <Switch 
                          checked={notifications.news}
                          onCheckedChange={(checked) => setNotifications({...notifications, news: checked})}
                        />
                      </div>
                      <div className="space-y-3 pt-4">
                        <Label className="text-sm font-medium text-gray-400">Email Frequency</Label>
                        <Select defaultValue="immediate">
                          <SelectTrigger className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                            <SelectItem value="immediate" className="text-white">Immediate</SelectItem>
                            <SelectItem value="hourly" className="text-white">Hourly Digest</SelectItem>
                            <SelectItem value="daily" className="text-white">Daily Digest</SelectItem>
                            <SelectItem value="weekly" className="text-white">Weekly Summary</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="appearance">
              <Card className="chart-container">
                <CardHeader>
                  <CardTitle className="text-white">Theme & Display</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Theme</Label>
                      <Select value={theme} onValueChange={(value: "light" | "dark") => setTheme(value)}>
                        <SelectTrigger className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                          <SelectItem value="dark" className="text-white">Dark Theme</SelectItem>
                          <SelectItem value="light" className="text-white">Light Theme</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Chart Style</Label>
                      <Select defaultValue="candlestick">
                        <SelectTrigger className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                          <SelectItem value="candlestick" className="text-white">Candlestick</SelectItem>
                          <SelectItem value="line" className="text-white">Line Chart</SelectItem>
                          <SelectItem value="bar" className="text-white">Bar Chart</SelectItem>
                          <SelectItem value="area" className="text-white">Area Chart</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label className="text-sm font-medium text-gray-400">Default Time Frame</Label>
                      <Select defaultValue="1D">
                        <SelectTrigger className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                          <SelectItem value="1H" className="text-white">1 Hour</SelectItem>
                          <SelectItem value="4H" className="text-white">4 Hours</SelectItem>
                          <SelectItem value="1D" className="text-white">1 Day</SelectItem>
                          <SelectItem value="1W" className="text-white">1 Week</SelectItem>
                          <SelectItem value="1M" className="text-white">1 Month</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-white font-medium">Show real-time prices</span>
                        <div className="text-sm text-gray-400">Display live price updates</div>
                      </div>
                      <Switch defaultChecked />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-white font-medium">Compact view</span>
                        <div className="text-sm text-gray-400">Reduce spacing and font sizes</div>
                      </div>
                      <Switch />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="api">
              <div className="space-y-6">
                <Card className="chart-container border-[var(--warning-yellow)]">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center">
                      <AlertTriangle className="w-5 h-5 warning-text mr-2" />
                      API Access
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="p-4 bg-[var(--warning-yellow)] bg-opacity-10 border border-[var(--warning-yellow)] rounded-lg">
                        <p className="text-sm warning-text">
                          <strong>Security Warning:</strong> API keys provide programmatic access to your account. 
                          Keep them secure and never share them publicly.
                        </p>
                      </div>
                      
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                          <Label className="text-sm font-medium text-gray-400">API Key</Label>
                          <div className="mt-2 p-3 bg-[var(--carbon-gray-80)] border border-[var(--carbon-gray-70)] rounded font-mono text-sm text-white">
                            ak_live_********************************
                          </div>
                        </div>
                        <div>
                          <Label className="text-sm font-medium text-gray-400">Secret Key</Label>
                          <div className="mt-2 p-3 bg-[var(--carbon-gray-80)] border border-[var(--carbon-gray-70)] rounded font-mono text-sm text-white">
                            sk_live_********************************
                          </div>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <h4 className="text-white font-medium">Permissions</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex items-center space-x-2">
                            <input type="checkbox" defaultChecked className="rounded" />
                            <span className="text-sm text-white">Read Portfolio</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <input type="checkbox" defaultChecked className="rounded" />
                            <span className="text-sm text-white">Execute Trades</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <input type="checkbox" className="rounded" />
                            <span className="text-sm text-white">Manage Strategies</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <input type="checkbox" className="rounded" />
                            <span className="text-sm text-white">Access Analytics</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex space-x-3">
                        <Button variant="outline" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                          Regenerate Keys
                        </Button>
                        <Button className="btn-primary">
                          Save Permissions
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="chart-container">
                  <CardHeader>
                    <CardTitle className="text-white">API Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-white">1,247</div>
                        <div className="text-sm text-gray-400">Requests Today</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-white">98.9%</div>
                        <div className="text-sm text-gray-400">Success Rate</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-white">45ms</div>
                        <div className="text-sm text-gray-400">Avg Response</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {isAdmin && (
              <TabsContent value="admin">
                <div className="space-y-6">
                  <Card className="chart-container border-[var(--warning-yellow)]">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center">
                        <Database className="w-5 h-5 warning-text mr-2" />
                        Broker URL Configuration
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        <div className="p-4 bg-[var(--warning-yellow)] bg-opacity-10 border border-[var(--warning-yellow)] rounded-lg">
                          <p className="text-sm warning-text">
                            <strong>Admin Only:</strong> These settings affect all users. Changes require system restart.
                          </p>
                        </div>

                        <div className="space-y-6">
                          <div>
                            <h4 className="text-white font-medium mb-4">Alpaca Trading URLs</h4>
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              <div>
                                <Label className="text-sm font-medium text-gray-400">Paper Trading URL</Label>
                                <Input
                                  defaultValue="https://paper-api.alpaca.markets"
                                  className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white font-mono text-sm"
                                />
                                <div className="text-xs text-gray-400 mt-1">ALPACA_BASE_URL</div>
                              </div>
                              <div>
                                <Label className="text-sm font-medium text-gray-400">Live Trading URL</Label>
                                <Input
                                  defaultValue="https://api.alpaca.markets"
                                  className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white font-mono text-sm"
                                />
                                <div className="text-xs text-gray-400 mt-1">ALPACA_LIVE_BASE_URL</div>
                              </div>
                            </div>
                          </div>

                          <Separator className="bg-[var(--carbon-gray-80)]" />

                          <div>
                            <h4 className="text-white font-medium mb-4">Zerodha Kite URLs</h4>
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              <div>
                                <Label className="text-sm font-medium text-gray-400">Paper Trading URL</Label>
                                <Input
                                  defaultValue="https://api.kite.trade"
                                  className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white font-mono text-sm"
                                />
                                <div className="text-xs text-gray-400 mt-1">ZERODHA_BASE_URL</div>
                              </div>
                              <div>
                                <Label className="text-sm font-medium text-gray-400">Live Trading URL</Label>
                                <Input
                                  defaultValue="https://api.kite.trade"
                                  className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white font-mono text-sm"
                                />
                                <div className="text-xs text-gray-400 mt-1">ZERODHA_LIVE_BASE_URL</div>
                              </div>
                            </div>
                          </div>

                          <Separator className="bg-[var(--carbon-gray-80)]" />

                          <div>
                            <h4 className="text-white font-medium mb-4">Global Settings</h4>
                            <div className="space-y-4">
                              <div className="flex items-center justify-between">
                                <div>
                                  <span className="text-white font-medium">Allow Live Trading</span>
                                  <div className="text-sm text-gray-400">Enable live trading globally for all users</div>
                                </div>
                                <Switch />
                              </div>
                              <div>
                                <Label className="text-sm font-medium text-gray-400">Default Trading Mode</Label>
                                <Select defaultValue="paper">
                                  <SelectTrigger className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                                    <SelectItem value="paper" className="text-white">Paper Trading</SelectItem>
                                    <SelectItem value="live" className="text-white">Live Trading</SelectItem>
                                  </SelectContent>
                                </Select>
                                <div className="text-xs text-gray-400 mt-1">DEFAULT_TRADING_MODE</div>
                              </div>
                            </div>
                          </div>

                          <div className="flex space-x-3">
                            <Button variant="outline" className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                              Test Connections
                            </Button>
                            <Button className="btn-primary">
                              Save Configuration
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="chart-container">
                    <CardHeader>
                      <CardTitle className="text-white">System Status</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="text-center">
                          <div className="text-2xl font-bold success-text">Active</div>
                          <div className="text-sm text-gray-400">Alpaca Connection</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold success-text">Active</div>
                          <div className="text-sm text-gray-400">Zerodha Connection</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-white">47</div>
                          <div className="text-sm text-gray-400">Active Users</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            )}
          </Tabs>
        </div>
      </main>
    </div>
  );
}
