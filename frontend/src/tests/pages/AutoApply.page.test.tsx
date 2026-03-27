import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const autoApplyMocks = vi.hoisted(() => ({
  listProfiles: vi.fn(),
  createProfile: vi.fn(),
  listRules: vi.fn(),
  createRule: vi.fn(),
  updateRule: vi.fn(),
  getStats: vi.fn(),
  pause: vi.fn(),
  run: vi.fn(),
  runs: vi.fn(),
}));

vi.mock("../../api/auto-apply", () => ({
  autoApplyApi: autoApplyMocks,
}));

import AutoApply from "../../pages/AutoApply";

describe("AutoApply page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    autoApplyMocks.listProfiles.mockResolvedValue({
      data: [
        {
          id: "profile-1",
          name: "Default Profile",
          full_name: "Jane Doe",
          email: "jobhunter@example.com",
          phone: "+1 555 0100",
          linkedin_url: "https://linkedin.com/in/janedoe",
          github_url: null,
          portfolio_url: null,
          cover_letter_template: "Hello {company}",
          is_active: true,
          created_at: "2026-03-20T12:00:00Z",
        },
      ],
    });
    autoApplyMocks.listRules.mockResolvedValue({
      data: [
        {
          id: "rule-1",
          profile_id: "profile-1",
          name: "Senior Frontend Roles",
          is_active: true,
          priority: 1,
          min_match_score: 80,
          required_keywords: ["React"],
          excluded_keywords: ["Intern"],
          required_companies: [],
          excluded_companies: [],
          experience_levels: [],
          remote_types: [],
          created_at: "2026-03-20T12:00:00Z",
        },
      ],
    });
    autoApplyMocks.getStats.mockResolvedValue({
      data: {
        total_runs: 4,
        successful: 3,
        failed: 1,
        pending: 0,
      },
    });
    autoApplyMocks.runs.mockResolvedValue({
      data: [
        {
          id: "run-1",
          job_id: "job-12345678",
          rule_id: "rule-1",
          status: "completed",
          ats_provider: "greenhouse",
          fields_filled: { email: "filled" },
          fields_missed: [],
          error_message: null,
          started_at: "2026-03-22T10:00:00Z",
          completed_at: "2026-03-22T10:05:00Z",
        },
      ],
    });
    autoApplyMocks.createProfile.mockResolvedValue({ data: null });
    autoApplyMocks.createRule.mockResolvedValue({ data: null });
    autoApplyMocks.updateRule.mockResolvedValue({ data: null });
    autoApplyMocks.pause.mockResolvedValue({ data: { status: "paused" } });
    autoApplyMocks.run.mockResolvedValue({ data: { status: "queued" } });
  });

  it("renders profile data and stats across the main auto-apply tabs", async () => {
    const user = userEvent.setup();

    renderWithProviders(<AutoApply />);

    expect(await screen.findByText("Default Profile")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Auto Apply/i })).toBeInTheDocument();
    expect(screen.getByText("jobhunter@example.com")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Statistics/i }));

    expect(await screen.findByText("Total Runs")).toBeInTheDocument();
    expect(screen.getByText("Successful")).toBeInTheDocument();
    expect(screen.getByText("Summary")).toBeInTheDocument();
  });

  it("exposes operator controls and triggers run and pause actions", async () => {
    const user = userEvent.setup();

    renderWithProviders(<AutoApply />);

    expect(await screen.findByText("Operator controls")).toBeInTheDocument();
    expect(screen.getByText("Latest run")).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: /^run now$/i })[0]);
    expect(autoApplyMocks.run).toHaveBeenCalledTimes(1);

    await user.click(screen.getAllByRole("button", { name: /^pause$/i })[0]);
    expect(autoApplyMocks.pause).toHaveBeenCalledTimes(1);
  });
});
