export type Trade = {
    id: string;
    symbol: string;
    side: "BUY" | "SELL";
    quantity: number;
    price: string;      // keep as string if backend returns strings
    value: string;
    status: "FILLED" | "PENDING" | "CANCELED";
    createdAt?: string; // ISO string
  };
  
  export type AllocationItem = {
    name: string;
    value: number;
    color?: string;
  };
  
  export type AlpacaAccount = {
    account_number: string;
    status: string;
    buying_power: string;
    cash: string;
    equity: string;
    // add fields as needed
  };
  
  export type PlatformInfo = {
    name: string;
    description?: string;
    version?: string;
    last_updated?: string;
  };
  
  export type PortfolioStatusItem = {
    symbol: string;
    quantity: number;
    value: number | string;
  };
  