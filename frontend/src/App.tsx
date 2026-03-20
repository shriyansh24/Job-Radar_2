import React, { Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import AuthGuard from "./components/layout/AuthGuard";
import ErrorBoundary from "./components/ErrorBoundary";
import PageLoader from "./components/ui/PageLoader";
import { ToastContainer } from "./components/ui/Toast";

const Login = React.lazy(() => import("./pages/Login"));
const Onboarding = React.lazy(() => import("./pages/Onboarding"));
const Dashboard = React.lazy(() => import("./pages/Dashboard"));
const JobBoard = React.lazy(() => import("./pages/JobBoard"));
const Pipeline = React.lazy(() => import("./pages/Pipeline"));
const AutoApply = React.lazy(() => import("./pages/AutoApply"));
const ResumeBuilder = React.lazy(() => import("./pages/ResumeBuilder"));
const InterviewPrep = React.lazy(() => import("./pages/InterviewPrep"));
const SalaryInsights = React.lazy(() => import("./pages/SalaryInsights"));
const DocumentVault = React.lazy(() => import("./pages/DocumentVault"));
const Analytics = React.lazy(() => import("./pages/Analytics"));
const Profile = React.lazy(() => import("./pages/Profile"));
const Settings = React.lazy(() => import("./pages/Settings"));
const Admin = React.lazy(() => import("./pages/Admin"));
const Companies = React.lazy(() => import("./pages/Companies"));
const Sources = React.lazy(() => import("./pages/Sources"));
const CanonicalJobs = React.lazy(() => import("./pages/CanonicalJobs"));
const SearchExpansion = React.lazy(() => import("./pages/SearchExpansion"));
const Targets = React.lazy(() => import("./pages/Targets"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes — data stays fresh during navigation
      gcTime: 10 * 60 * 1000,        // 10 minutes — keep cache in memory longer
      retry: 1,
      refetchOnWindowFocus: false,   // Don't refetch when user alt-tabs back
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/onboarding" element={<Onboarding />} />
              <Route
                element={
                  <AuthGuard>
                    <AppShell />
                  </AuthGuard>
                }
              >
                <Route index element={<Dashboard />} />
                <Route path="/jobs" element={<JobBoard />} />
                <Route path="/pipeline" element={<Pipeline />} />
                <Route path="/auto-apply" element={<AutoApply />} />
                <Route path="/resume" element={<ResumeBuilder />} />
                <Route path="/interview" element={<InterviewPrep />} />
                <Route path="/salary" element={<SalaryInsights />} />
                <Route path="/vault" element={<DocumentVault />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/admin" element={<Admin />} />
                <Route path="/companies" element={<Companies />} />
                <Route path="/sources" element={<Sources />} />
                <Route path="/canonical-jobs" element={<CanonicalJobs />} />
                <Route path="/search-expansion" element={<SearchExpansion />} />
                <Route path="/targets" element={<Targets />} />
              </Route>
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </BrowserRouter>
      <ToastContainer />
    </QueryClientProvider>
  );
}
