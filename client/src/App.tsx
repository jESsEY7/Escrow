import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, RequireAuth } from "@/contexts/AuthContext";

// Public pages
import Home from "@/pages/home";
import NotFound from "@/pages/not-found";
import Login from "@/pages/auth/login";

// Protected pages
import Dashboard from "@/pages/dashboard";
import EscrowList from "@/pages/escrows/index";
import EscrowDetail from "@/pages/escrows/[id]";
import CreateEscrow from "@/pages/escrows/new";
import DisputeList from "@/pages/disputes/index";
import CreateDispute from "@/pages/disputes/new";
import AdminDashboard from "@/pages/admin/index";
import AdminUsers from "@/pages/admin/users";

function Router() {
  return (
    <Switch>
      {/* Public routes */}
      <Route path="/" component={Home} />
      <Route path="/login" component={Login} />

      {/* Protected routes - Dashboard */}
      <Route path="/dashboard">
        <RequireAuth>
          <Dashboard />
        </RequireAuth>
      </Route>

      {/* Escrow routes */}
      <Route path="/escrows">
        <RequireAuth>
          <EscrowList />
        </RequireAuth>
      </Route>
      <Route path="/escrows/new">
        <RequireAuth>
          <CreateEscrow />
        </RequireAuth>
      </Route>
      <Route path="/escrows/:id">
        {(params) => (
          <RequireAuth>
            <EscrowDetail />
          </RequireAuth>
        )}
      </Route>

      {/* Dispute routes */}
      <Route path="/disputes">
        <RequireAuth>
          <DisputeList />
        </RequireAuth>
      </Route>
      <Route path="/disputes/new">
        <RequireAuth>
          <CreateDispute />
        </RequireAuth>
      </Route>

      {/* Admin routes */}
      <Route path="/admin">
        <RequireAuth>
          <AdminDashboard />
        </RequireAuth>
      </Route>
      <Route path="/admin/users">
        <RequireAuth>
          <AdminUsers />
        </RequireAuth>
      </Route>

      {/* Fallback */}
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
