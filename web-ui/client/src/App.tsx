// =====================================================
// Updated App.tsx with Authentication
// =====================================================
import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/hooks/use-theme";
import { AuthProvider } from "@/contexts/AuthContext";
import { TradingModeProvider } from "@/contexts/TradingModeContext";
import { ProtectedRoute, PublicRoute } from "@/components/auth";

// Existing pages
import NotFound from "./pages/not-found";
import Dashboard from "./pages/dashboard";
import Portfolio from "./pages/portfolio";
import Trading from "./pages/trading";
import Algorithms from "./pages/algorithms";
import AlgorithmDetail from "./pages/algorithms/[id]";
import Analytics from "./pages/analytics";
import Settings from "./pages/settings";
import Smallcases from "./pages/smallcases";

// New auth pages
import { LoginPage, RegisterPage, ForgotPasswordPage } from "./pages/auth";

function Router() {
  return (
    <Switch>
      {/* Public Auth Routes */}
      <Route path="/auth/login">
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      </Route>
      
      <Route path="/auth/register">
        <PublicRoute>
          <RegisterPage />
        </PublicRoute>
      </Route>
      
      <Route path="/auth/forgot-password">
        <PublicRoute>
          <ForgotPasswordPage />
        </PublicRoute>
      </Route>

      {/* Protected Routes */}
      <Route path="/">
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      </Route>
      
      <Route path="/portfolio">
        <ProtectedRoute>
          <Portfolio />
        </ProtectedRoute>
      </Route>
      
      <Route path="/trading">
        <ProtectedRoute>
          <Trading />
        </ProtectedRoute>
      </Route>
      
      <Route path="/algorithms/:id">
        <ProtectedRoute>
          <AlgorithmDetail />
        </ProtectedRoute>
      </Route>

      <Route path="/algorithms">
        <ProtectedRoute>
          <Algorithms />
        </ProtectedRoute>
      </Route>

      <Route path="/analytics">
        <ProtectedRoute>
          <Analytics />
        </ProtectedRoute>
      </Route>
      
      <Route path="/settings">
        <ProtectedRoute>
          <Settings />
        </ProtectedRoute>
      </Route>
      
      <Route path="/smallcases">
        <ProtectedRoute>
          <Smallcases />
        </ProtectedRoute>
      </Route>

      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <AuthProvider>
            <TradingModeProvider>
              <div className="trading-platform">
                <Toaster />
                <Router />
              </div>
            </TradingModeProvider>
          </AuthProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
