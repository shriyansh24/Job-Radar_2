import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const analyticsMocks = vi.hoisted(() => ({
  overview: vi.fn(),
  daily: vi.fn(),
  sources: vi.fn(),
  skills: vi.fn(),
  funnel: vi.fn(),
  patterns: vi.fn(),
}));

vi.mock("../../api/analytics", () => ({
  analyticsApi: analyticsMocks,
}));

vi.mock("../../components/analytics/AnalyticsCharts", () => ({
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

import Analytics from "../../pages/Analytics";

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
    analyticsMocks.patterns.mockResolvedValue({
      data: {
        callback_rate_by_company_size: [
          {
            size_bucket: "small",
            total_applications: 3,
            callbacks: 2,
            callback_rate: 66.7,
          },
        ],
        conversion_funnel: [{ stage: "applied", count: 3 }],
        response_time_patterns: [
          {
            avg_days_to_response: 2.5,
            sample_size: 3,
            warning: null,
          },
        ],
        best_application_timing: [
          {
            day_of_week: "Tuesday",
            total_applications: 3,
            callbacks: 2,
            callback_rate: 66.7,
          },
        ],
        company_ghosting_rate: [
          {
            company: "Acme",
            total_applications: 3,
            ghosted: 1,
            ghosting_rate: 33.3,
          },
        ],
        skill_gap_detection: [{ skill: "GraphQL", demand_count: 4 }],
      },
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
    expect(screen.getByText("Application patterns")).toBeInTheDocument();
    expect(screen.getByText("small - 66.7%")).toBeInTheDocument();
    expect(await screen.findByTestId("analytics-charts")).toHaveTextContent(
      "daily:1;funnel:1;sources:1;skills:1"
    );

    await waitFor(() => {
      expect(analyticsMocks.overview).toHaveBeenCalledTimes(1);
      expect(analyticsMocks.daily).toHaveBeenCalledWith(30);
      expect(analyticsMocks.sources).toHaveBeenCalledTimes(1);
      expect(analyticsMocks.skills).toHaveBeenCalledWith(10);
      expect(analyticsMocks.funnel).toHaveBeenCalledTimes(1);
      expect(analyticsMocks.patterns).toHaveBeenCalledTimes(1);
    });
  });

  it("renders empty-state analytics surfaces when source and skill data are empty", async () => {
    analyticsMocks.overview.mockResolvedValue({
      data: {
        total_jobs: 0,
        total_applications: 0,
        total_interviews: 0,
        total_offers: 0,
        applications_by_status: {},
        response_rate: 0,
        avg_days_to_response: 0,
        jobs_scraped_today: 0,
        enriched_jobs: 0,
      },
    });
    analyticsMocks.daily.mockResolvedValue({ data: [] });
    analyticsMocks.sources.mockResolvedValue({ data: [] });
    analyticsMocks.skills.mockResolvedValue({ data: [] });
    analyticsMocks.funnel.mockResolvedValue({ data: [] });
    analyticsMocks.patterns.mockResolvedValue({
      data: {
        callback_rate_by_company_size: [],
        conversion_funnel: [],
        response_time_patterns: [],
        best_application_timing: [],
        company_ghosting_rate: [],
        skill_gap_detection: [],
      },
    });

    renderWithProviders(<Analytics />);

    expect(await screen.findByRole("heading", { name: "Analytics" })).toBeInTheDocument();
    expect(screen.getByText("30 day window")).toBeInTheDocument();
    expect(await screen.findByText("No skill data yet")).toBeInTheDocument();
    expect(screen.getByText("No source quality yet")).toBeInTheDocument();
    expect(await screen.findByText("No pattern data yet")).toBeInTheDocument();
    expect(await screen.findByTestId("analytics-charts")).toHaveTextContent(
      "daily:0;funnel:0;sources:0;skills:0"
    );
  });
});
