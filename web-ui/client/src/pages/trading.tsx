import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";

export default function Trading() {
  const [orderForm, setOrderForm] = useState({
    symbol: "",
    side: "BUY",
    orderType: "MARKET",
    quantity: "",
    price: "",
  });

  const handleInputChange = (field: string, value: string) => {
    setOrderForm(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      
      <main className="flex-1 overflow-hidden">
        <Header 
          title="Trading" 
          subtitle="Execute trades and manage orders"
        />
        
        <div className="p-6 h-full overflow-y-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Order Entry */}
            <div className="lg:col-span-1">
              <Card className="chart-container">
                <CardHeader>
                  <CardTitle className="text-white">Place Order</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-400">Symbol</Label>
                    <Input
                      placeholder="e.g., AAPL"
                      value={orderForm.symbol}
                      onChange={(e) => handleInputChange("symbol", e.target.value)}
                      className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                    />
                  </div>

                  <div>
                    <Label className="text-sm font-medium text-gray-400">Order Type</Label>
                    <Select value={orderForm.orderType} onValueChange={(value) => handleInputChange("orderType", value)}>
                      <SelectTrigger className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                        <SelectItem value="MARKET" className="text-white">Market</SelectItem>
                        <SelectItem value="LIMIT" className="text-white">Limit</SelectItem>
                        <SelectItem value="STOP" className="text-white">Stop</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Side</Label>
                      <Select value={orderForm.side} onValueChange={(value) => handleInputChange("side", value)}>
                        <SelectTrigger className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)]">
                          <SelectItem value="BUY" className="text-white">Buy</SelectItem>
                          <SelectItem value="SELL" className="text-white">Sell</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Quantity</Label>
                      <Input
                        type="number"
                        placeholder="100"
                        value={orderForm.quantity}
                        onChange={(e) => handleInputChange("quantity", e.target.value)}
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                  </div>

                  {orderForm.orderType !== "MARKET" && (
                    <div>
                      <Label className="text-sm font-medium text-gray-400">Price</Label>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={orderForm.price}
                        onChange={(e) => handleInputChange("price", e.target.value)}
                        className="mt-2 bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white"
                      />
                    </div>
                  )}

                  <div className="space-y-2 pt-4">
                    <Button className="w-full btn-primary">
                      Place Order
                    </Button>
                    <Button variant="outline" className="w-full bg-[var(--carbon-gray-80)] border-[var(--carbon-gray-70)] text-white hover:bg-[var(--carbon-gray-70)]">
                      Clear Form
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Market Data */}
              <Card className="chart-container mt-6">
                <CardHeader>
                  <CardTitle className="text-white">Market Data</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center py-2 border-b border-[var(--carbon-gray-80)]">
                      <span className="text-sm text-gray-400">AAPL</span>
                      <div className="text-right">
                        <div className="text-white font-medium">$180.45</div>
                        <div className="text-sm success-text">+1.19%</div>
                      </div>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-[var(--carbon-gray-80)]">
                      <span className="text-sm text-gray-400">MSFT</span>
                      <div className="text-right">
                        <div className="text-white font-medium">$389.50</div>
                        <div className="text-sm success-text">+1.40%</div>
                      </div>
                    </div>
                    <div className="flex justify-between items-center py-2">
                      <span className="text-sm text-gray-400">TSLA</span>
                      <div className="text-right">
                        <div className="text-white font-medium">$265.30</div>
                        <div className="text-sm danger-text">-0.97%</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Orders and Positions */}
            <div className="lg:col-span-2">
              <Tabs defaultValue="orders" className="w-full">
                <TabsList className="grid w-full grid-cols-3 bg-[var(--carbon-gray-90)]">
                  <TabsTrigger value="orders" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">Open Orders</TabsTrigger>
                  <TabsTrigger value="filled" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">Order History</TabsTrigger>
                  <TabsTrigger value="positions" className="text-white data-[state=active]:bg-[var(--carbon-blue)]">Positions</TabsTrigger>
                </TabsList>

                <TabsContent value="orders" className="mt-6">
                  <Card className="chart-container">
                    <CardHeader>
                      <CardTitle className="text-white">Open Orders</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-center py-8">
                        <p className="text-gray-400">No open orders</p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="filled" className="mt-6">
                  <Card className="chart-container">
                    <CardHeader>
                      <CardTitle className="text-white">Order History</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="text-left border-b border-[var(--carbon-gray-80)]">
                              <th className="pb-3 text-sm font-medium text-gray-400">Time</th>
                              <th className="pb-3 text-sm font-medium text-gray-400">Symbol</th>
                              <th className="pb-3 text-sm font-medium text-gray-400">Side</th>
                              <th className="pb-3 text-sm font-medium text-gray-400">Quantity</th>
                              <th className="pb-3 text-sm font-medium text-gray-400">Price</th>
                              <th className="pb-3 text-sm font-medium text-gray-400">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr className="border-b border-[var(--carbon-gray-80)]">
                              <td className="py-3 text-sm text-white">09:34:12</td>
                              <td className="py-3 text-sm font-medium text-white">AAPL</td>
                              <td className="py-3">
                                <Badge className="bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]">
                                  BUY
                                </Badge>
                              </td>
                              <td className="py-3 text-sm text-white">500</td>
                              <td className="py-3 text-sm text-white">$178.32</td>
                              <td className="py-3">
                                <Badge className="bg-[var(--success-green)] bg-opacity-20 text-[var(--success-green)]">
                                  FILLED
                                </Badge>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="positions" className="mt-6">
                  <Card className="chart-container">
                    <CardHeader>
                      <CardTitle className="text-white">Current Positions</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-center py-8">
                        <p className="text-gray-400">View detailed positions in the Portfolio section</p>
                        <Button className="mt-4 btn-primary" onClick={() => window.location.href = '/portfolio'}>
                          Go to Portfolio
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
