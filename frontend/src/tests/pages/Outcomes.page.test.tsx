import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const outcomesMocks = vi.hoisted(() => ({
  getStats: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  getCompanyInsights: vi.fn(),
}));

const pipelineMocks = vi.hoisted(() => ({
  list: vi.fn(),
}));

vi.mock("../../api/outcomes", () => ({
  outcomesApi: outcomesMocks,
}));

vi.mock("../../api/pipeline", () => ({
  pipelineApi: pipelineMocks,
}));

import Outcomes from "../../pages/Outcomes";

describe("Outcomes page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    outcomesMocks.getStats.mockResolvedValue({
      data: {
        total_applications: 12,
        total_outcomes: 5,
        avg_days_to_response: 4.5,
        ghosting_rate: 0.25,
        response_rate: 0.5,
        offer_rate: 0.1,
        avg_offer_amount: 170000,
        top_rejection_reasons: [{ reason: "role fit", count: 2 }],
        stage_distribution: { applied: 12 },
      },
    });
    outcomesMocks.get.mockRejectedValue({ response: { status: 404 } });
    pipelineMocks.list.mockResolvedValue({
      data: {
        items: [
          {
            id: "app-1",
            company_name: "Acme",
            position_title: "Platform Engineer",
          },
        ],
      },
    });
  });

  it("renders stats and the outcome capture workspace", async () => {
    renderWithProviders(<Outcomes />);

    expect(await screen.findByRole("heading", { name: "Outcomes" })).toBeInTheDocument();
    expect(screen.getByText("Response Rate")).toBeInTheDocument();
    expect(screen.getByText("Ghost Rate")).toBeInTheDocument();
    expect(screen.getByText("Keep it honest")).toBeInTheDocument();
  });
});
