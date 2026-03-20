import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../api/jobs", () => ({
  jobsApi: {
    list: () => Promise.resolve({ data: { items: [], total: 0, total_pages: 0 } }),
    get: () => Promise.resolve({ data: null }),
  },
}));

import JobBoard from "../pages/JobBoard";

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

describe("JobBoard", () => {
  it("renders search input", () => {
    renderWithProviders(<JobBoard />);
    expect(screen.getByPlaceholderText("Search jobs...")).toBeInTheDocument();
  });

  it("shows empty state when no jobs are returned", async () => {
    renderWithProviders(<JobBoard />);
    expect(await screen.findByText("No jobs found")).toBeInTheDocument();
    expect(
      screen.getByText("Try adjusting your search or filters")
    ).toBeInTheDocument();
  });
});
