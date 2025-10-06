// =====================================================
// src/types/auth.ts - Type definitions
// =====================================================

export interface User {
    id: string;
    email: string;
    username: string;
    first_name?: string;
    last_name?: string;
    email_verified: boolean;
    kyc_status: string;
    account_status: string;
    region: string;
    trading_mode: 'paper' | 'live';
    created_at: string;
  }
  
  export interface AuthContextType {
    user: User | null;
    login: (email: string, password: string) => Promise<void>;
    register: (userData: RegisterData) => Promise<void>;
    logout: () => void;
    isLoading: boolean;
    isAuthenticated: boolean;
  }
  
  export interface RegisterData {
    email: string;
    username: string;
    password: string;
    first_name: string;
    last_name: string;
  }
  
  export interface LoginData {
    email: string;
    password: string;
  }