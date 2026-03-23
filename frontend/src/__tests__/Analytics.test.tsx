import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const analyticsMocks = vi.hoisted(() => ({
  overview: vi.fn(),
  daily: vi.fn(),
  sources: vi.fn(),
  skills: vi.fn(),
  funnel: vi.fn(),
}));

vi.mock("../api/analytics", () => ({
  analyticsApi: analyticsMocks,
}));

vi.mock("../components/analytics/AnalyticsCharts", () => ({
  default: ({
    daily,
    funnel,
    sources,
    skills,
  }: {
    daily?: unknown[];
    funnel?: unknown[];
    sources?: unknown[];
    skills?: unknown[];
  }) => (
    <div data-testid="analytics-charts">
      {`daily:${daily?.length ?? 0};funnel:${funnel?.length ?? 0};sources:${sources?.length ?? 0};skills:${skills?.length ?? 0}`}
    </div>
  ),
}));

import Analytics from "../pages/Analytics";

function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Analytics page", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    analyticsMocks.overview.mockResolvedValue({
      data: {
        total_jobs: 1234,
        total_applications: 89,
        total_interviews: 12,
        total_offers: 3,
        applications_by_status: { applied: 89 },
        response_rate: 0.33,
        avg_days_to_response: 4.5,
        jobs_scraped_today: 18,
        enriched_jobs: 240,
      },
    });
    analyticsMocks.daily.mockResolvedValue({
      data: [{ date: "2026-03-20", jobs_scraped: 10, applications: 2 }],
    });
    analyticsMocks.sources.mockResolvedValue({
      data: [
        {
          source: "LinkedIn",
          total_jobs: 150,
          quality_score: 0.82,
          avg_match_score: 0.74,
        },
      ],
    });
    analyticsMocks.skills.mockResolvedValue({
      data: [{ skill: "TypeScript", count: 12, percentage: 0.5 }],
    });
    analyticsMocks.funnel.mockResolvedValue({
      data: [{ stage: "Applied", count: 89 }],
    });
  });

  it("loads analytics datasets and renders formatted stats and source quality", async () => {
    renderWithProviders(<Analytics />);

    expect(await screen.findByText("1,234")).toBeInTheDocument();
    expect(screen.getByText("89")).toBeInTheDocument();
    expect(screen.getByText("33%")).toBeInTheDocument();
    expect(screen.getByText("4.5")).toBeInTheDocument();
    expect(screen.getByText("LinkedIn")).toBeInTheDocument();
    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(screen.getByText("74%")).toBeInTheDocument();
    expect(await screen.findByTestId("analytics-charts")).toHaveTextContent(
      "daily:1;funnel:1;sources:1;skills:1"
    );

    await waitFor(() => {
      expect(analyticsMocks.overview).toHaveBeenCalledTimes(1);
      expect(analyticsMocks.daily).toHaveBeenCalledWith(30);
      expect(analyticsMocks.sources).toHaveBeenCalledTimes(1);
      expect(analyticsMocks.skills).toHaveBeenCalledWith(10);
      expect(analyticsMocks.funnel).toHaveBeenCalledTimes(1);
    });
  });
});
