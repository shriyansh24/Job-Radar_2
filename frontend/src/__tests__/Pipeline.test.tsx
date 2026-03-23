import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./testUtils";

const pipelineMocks = vi.hoisted(() => ({
  pipeline: vi.fn(),
  transition: vi.fn(),
}));

vi.mock("../api/pipeline", () => ({
  pipelineApi: pipelineMocks,
}));

import Pipeline from "../pages/Pipeline";

describe("Pipeline page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    pipelineMocks.pipeline.mockResolvedValue({
      data: {
        saved: [
          {
            id: "app-1",
            position_title: "Backend Engineer",
            company_name: "Acme",
            status: "saved",
            updated_at: "2026-03-22T10:00:00Z",
            source: "LinkedIn",
            salary_offered: null,
            notes: "",
          },
        ],
        applied: [
          {
            id: "app-2",
            position_title: "Frontend Engineer",
            company_name: "Beta",
            status: "applied",
            updated_at: "2026-03-22T10:00:00Z",
            source: "Wellfound",
            salary_offered: 180000,
            notes: "Initial recruiter conversation booked.",
          },
        ],
        screening: [],
        interviewing: [],
        offer: [],
        accepted: [],
        rejected: [],
        withdrawn: [],
      },
    });
    pipelineMocks.transition.mockResolvedValue({ data: null });
  });

  it("renders the current pipeline board and selected application details", async () => {
    renderWithProviders(<Pipeline />);

    expect(await screen.findByRole("heading", { name: "Pipeline" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /run auto-apply/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /open copilot/i })).toBeInTheDocument();
    expect(await screen.findByText("Saved")).toBeInTheDocument();
    expect(await screen.findByText("Applied")).toBeInTheDocument();
    expect((await screen.findAllByText("Backend Engineer")).length).toBeGreaterThan(0);
    expect(screen.getByText("Frontend Engineer")).toBeInTheDocument();
    expect(screen.getByText("Selected application")).toBeInTheDocument();
    expect(screen.getAllByText("Acme").length).toBeGreaterThan(0);
    expect(screen.getByText("LinkedIn")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /^advance$/i }).length).toBeGreaterThan(0);
  });
});
