import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/hooks/use-theme";
import NotFound from "./pages/not-found";
import Dashboard from "./pages/dashboard";
import Portfolio from "./pages/portfolio";
import Trading from "./pages/trading";
import Algorithms from "./pages/algorithms";
import Strategies from "./pages/strategies";
import Analytics from "./pages/analytics";
import Settings from "./pages/settings";
import Smallcases from "./pages/smallcases";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/portfolio" component={Portfolio} />
      <Route path="/trading" component={Trading} />
      <Route path="/algorithms" component={Algorithms} />
      <Route path="/strategies" component={Strategies} />
      <Route path="/analytics" component={Analytics} />
      <Route path="/settings" component={Settings} />
      <Route path="/smallcases" component={Smallcases} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <div className="trading-platform">
            <Toaster />
            <Router />
          </div>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
