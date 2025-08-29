import React, { useState } from 'react';
import { useBrokers, useAccountInfo, usePositions, useBalance, useTradingHealth } from '../hooks/useTrading';
import { usePortfolios } from '../hooks/usePortfolio';

interface TradingDashboardProps {
  className?: string;
}

export const TradingDashboard: React.FC<TradingDashboardProps> = ({ className }) => {
  const [selectedBroker, setSelectedBroker] = useState<string>('');
  
  // Fetch data using our custom hooks
  const { data: brokersData, isLoading: brokersLoading, error: brokersError } = useBrokers();
  const { data: portfoliosData, isLoading: portfoliosLoading } = usePortfolios();
  const { data: healthData } = useTradingHealth();
  
  // Conditional queries based on selected broker
  const { data: accountData, isLoading: accountLoading } = useAccountInfo(selectedBroker, !!selectedBroker);
  const { data: positionsData, isLoading: positionsLoading } = usePositions(selectedBroker, !!selectedBroker);
  const { data: balanceData, isLoading: balanceLoading } = useBalance(selectedBroker, !!selectedBroker);

  const brokers = brokersData?.data || [];
  const portfolios = portfoliosData?.data || [];

  return (
    <div className={`trading-dashboard ${className || ''}`}>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Dashboard</h1>
        <p className="text-gray-600">Monitor your trading accounts and portfolios</p>
      </div>

      {/* Health Status */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-2">System Health</h2>
        <div className="flex items-center space-x-4">
          <div className={`px-3 py-1 rounded-full text-sm ${
            healthData?.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {healthData?.success ? 'Healthy' : 'Issues Detected'}
          </div>
          {healthData?.data && (
            <span className="text-sm text-gray-600">
              Active Brokers: {healthData.data.active_brokers}
            </span>
          )}
        </div>
      </div>

      {/* Broker Selection */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Connected Brokers</h2>
        
        {brokersLoading && <div className="text-gray-500">Loading brokers...</div>}
        {brokersError && <div className="text-red-500">Error loading brokers</div>}
        
        {brokers.length > 0 ? (
          <div className="space-y-2">
            {brokers.map((broker: any, index: number) => (
              <div 
                key={index}
                className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedBroker === broker.name 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedBroker(broker.name)}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-medium">{broker.name}</h3>
                    <p className="text-sm text-gray-600">
                      {broker.broker_type} • {broker.paper_trading ? 'Paper Trading' : 'Live Trading'}
                    </p>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs ${
                    broker.status === 'connected' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {broker.status}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500">No brokers connected</div>
        )}
      </div>

      {/* Account Information */}
      {selectedBroker && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
          {/* Account Info */}
          <div className="p-4 bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">Account Info</h3>
            {accountLoading ? (
              <div className="text-gray-500">Loading...</div>
            ) : accountData?.success ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Account ID:</span>
                  <span className="font-medium">{accountData.data?.account_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className="font-medium">{accountData.data?.status}</span>
                </div>
              </div>
            ) : (
              <div className="text-red-500">Failed to load account info</div>
            )}
          </div>

          {/* Balance */}
          <div className="p-4 bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">Balance</h3>
            {balanceLoading ? (
              <div className="text-gray-500">Loading...</div>
            ) : balanceData?.success ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Cash:</span>
                  <span className="font-medium">${balanceData.data?.cash?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Buying Power:</span>
                  <span className="font-medium">${balanceData.data?.buying_power?.toFixed(2)}</span>
                </div>
              </div>
            ) : (
              <div className="text-red-500">Failed to load balance</div>
            )}
          </div>

          {/* Positions Summary */}
          <div className="p-4 bg-white rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">Positions</h3>
            {positionsLoading ? (
              <div className="text-gray-500">Loading...</div>
            ) : positionsData?.success ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Positions:</span>
                  <span className="font-medium">{positionsData.data?.length || 0}</span>
                </div>
                {positionsData.data?.slice(0, 3).map((position: any, index: number) => (
                  <div key={index} className="flex justify-between text-sm">
                    <span className="text-gray-600">{position.symbol}:</span>
                    <span className="font-medium">{position.quantity}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-red-500">Failed to load positions</div>
            )}
          </div>
        </div>
      )}

      {/* Portfolios */}
      <div className="p-4 bg-white rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Portfolios</h2>
        
        {portfoliosLoading ? (
          <div className="text-gray-500">Loading portfolios...</div>
        ) : portfolios.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {portfolios.map((portfolio: any) => (
              <div key={portfolio.id} className="p-3 border rounded-lg">
                <h3 className="font-medium">{portfolio.name}</h3>
                <p className="text-sm text-gray-600 mb-2">{portfolio.description}</p>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Value:</span>
                  <span className="font-medium">${portfolio.total_value?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Cash:</span>
                  <span className="font-medium">${portfolio.cash_balance?.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500">No portfolios found</div>
        )}
      </div>
    </div>
  );
};
