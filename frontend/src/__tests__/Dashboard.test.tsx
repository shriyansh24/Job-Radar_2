import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../api/analytics", () => ({
  analyticsApi: {
    overview: () =>
      Promise.resolve({
        data: {
          total_jobs: 42,
          total_applications: 10,
          total_interviews: 3,
          total_offers: 1,
          response_rate: 30,
          avg_days_to_response: 5,
        },
      }),
  },
}));

vi.mock("../api/jobs", () => ({
  jobsApi: {
    list: () => Promise.resolve({ data: { items: [], total: 0, total_pages: 0 } }),
  },
}));

vi.mock("../api/pipeline", () => ({
  pipelineApi: {
    pipeline: () => Promise.resolve({ data: {} }),
  },
}));

import Dashboard from "../pages/Dashboard";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Dashboard", () => {
  it("renders heading and stat cards after loading", async () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(await screen.findByText("42")).toBeInTheDocument();
    expect(screen.getByText("Total Jobs")).toBeInTheDocument();
    expect(screen.getByText("Applications")).toBeInTheDocument();
    expect(screen.getByText("Interviews")).toBeInTheDocument();
    expect(screen.getByText("Offers")).toBeInTheDocument();
  });

  it("shows quick action buttons", async () => {
    renderWithProviders(<Dashboard />);
    expect(await screen.findByText("Browse Jobs")).toBeInTheDocument();
    expect(screen.getByText("Add Application")).toBeInTheDocument();
    expect(screen.getByText("Upload Resume")).toBeInTheDocument();
  });
});
