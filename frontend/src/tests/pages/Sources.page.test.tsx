import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const phase7aMocks = vi.hoisted(() => ({
  listSourceHealth: vi.fn(),
}));

vi.mock("../../api/phase7a", () => ({
  sourceHealthApi: {
    list: phase7aMocks.listSourceHealth,
  },
  companiesApi: {
    list: vi.fn(),
  },
  searchExpansionApi: {
    expand: vi.fn(),
  },
}));

import Sources from "../../pages/Sources";

describe("Sources page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    phase7aMocks.listSourceHealth.mockResolvedValue([
      {
        id: "source-1",
        source_name: "LinkedIn",
        health_state: "healthy",
        quality_score: 0.84,
        total_jobs_found: 120,
        last_check_at: "2026-03-22T12:00:00Z",
        failure_count: 1,
        backoff_until: null,
        created_at: "2026-03-20T12:00:00Z",
      },
    ]);
  });

  it("renders source health cards from query data", async () => {
    renderWithProviders(<Sources />);

    expect(
      await screen.findByRole("heading", { name: /Source Health/i })
    ).toBeInTheDocument();
    expect(await screen.findByText("LinkedIn")).toBeInTheDocument();
    expect(screen.getByText("84%")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
  });
});
