import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/test-utils";

const pipelineMocks = vi.hoisted(() => ({
  pipeline: vi.fn(),
  transition: vi.fn(),
}));

vi.mock("../../api/pipeline", () => ({
  pipelineApi: pipelineMocks,
}));

import Pipeline from "../../pages/Pipeline";

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
        rejected: [
          {
            id: "app-3",
            position_title: "Platform Engineer",
            company_name: "Gamma",
            status: "rejected",
            updated_at: "2026-03-22T10:00:00Z",
            source: "Direct",
            salary_offered: null,
            notes: "Closed after final loop.",
          },
        ],
        withdrawn: [
          {
            id: "app-4",
            position_title: "Infra Engineer",
            company_name: "Delta",
            status: "withdrawn",
            updated_at: "2026-03-22T10:00:00Z",
            source: "Referral",
            salary_offered: null,
            notes: "Role paused internally.",
          },
        ],
      },
    });
    pipelineMocks.transition.mockResolvedValue({ data: null });
  });

  it("renders the current pipeline board and selected application details", async () => {
    renderWithProviders(<Pipeline />);

    expect(await screen.findByRole("heading", { name: "Pipeline" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^auto-apply$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^copilot$/i })).toBeInTheDocument();
    expect(await screen.findByText("Saved")).toBeInTheDocument();
    expect(await screen.findByText("Applied")).toBeInTheDocument();
    expect(await screen.findByText("Rejected")).toBeInTheDocument();
    expect(await screen.findByText("Withdrawn")).toBeInTheDocument();
    expect((await screen.findAllByText("Backend Engineer")).length).toBeGreaterThan(0);
    expect(screen.getByText("Frontend Engineer")).toBeInTheDocument();
    expect(screen.getByText("Platform Engineer")).toBeInTheDocument();
    expect(screen.getByText("Infra Engineer")).toBeInTheDocument();
    expect(screen.getByText("Details")).toBeInTheDocument();
    expect(screen.getAllByText("Acme").length).toBeGreaterThan(0);
    expect(screen.getAllByText("LinkedIn").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: /^advance$/i }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /move to withdrawn/i })).toBeInTheDocument();
  });
});
