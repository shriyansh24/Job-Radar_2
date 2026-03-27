import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/test-utils";

const scraperMocks = vi.hoisted(() => ({
  listTargets: vi.fn(),
  getTarget: vi.fn(),
  triggerBatch: vi.fn(),
  updateTarget: vi.fn(),
  triggerTarget: vi.fn(),
  releaseTarget: vi.fn(),
  importTargets: vi.fn(),
  stream: vi.fn(),
}));

vi.mock("../../api/scraper", () => ({
  scraperApi: scraperMocks,
}));

import Targets from "../../pages/Targets";

describe("Targets operator exposure", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    scraperMocks.listTargets.mockResolvedValue({
      data: {
        items: [
          {
            id: "target-1",
            url: "https://acme.example/jobs",
            company_name: "Acme",
            company_domain: "acme.example",
            source_kind: "career_page",
            ats_vendor: "greenhouse",
            ats_board_token: "acme",
            start_tier: 1,
            max_tier: 3,
            priority_class: "hot",
            schedule_interval_m: 60,
            enabled: true,
            quarantined: false,
            quarantine_reason: null,
            last_success_at: "2026-03-22T12:00:00Z",
            last_failure_at: null,
            last_success_tier: 2,
            last_http_status: 200,
            content_hash: "hash",
            consecutive_failures: 0,
            failure_count: 0,
            next_scheduled_at: "2026-03-24T12:00:00Z",
            lca_filings: 0,
            industry: "Software",
            created_at: "2026-03-01T12:00:00Z",
            updated_at: "2026-03-22T12:00:00Z",
          },
        ],
        total: 1,
      },
    });
    scraperMocks.triggerBatch.mockResolvedValue({
      data: {
        run_id: "run-1",
        targets_attempted: 1,
        targets_succeeded: 1,
        targets_failed: 0,
        jobs_found: 4,
        errors: [],
      },
    });
    scraperMocks.getTarget.mockResolvedValue({ data: null });
    scraperMocks.updateTarget.mockResolvedValue({ data: null });
    scraperMocks.triggerTarget.mockResolvedValue({ data: null });
    scraperMocks.releaseTarget.mockResolvedValue({ data: null });
    scraperMocks.importTargets.mockResolvedValue({
      data: { imported: 0, skipped: 0, errors: [] },
    });
    scraperMocks.stream.mockReturnValue("/api/v1/scraper/stream");
  });

  it("renders the live batch operator controls on mount", async () => {
    renderWithProviders(<Targets />);

    expect(await screen.findByRole("heading", { name: /Scrape Targets/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Import Targets/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Run target batch/i })).toBeInTheDocument();
    expect(screen.queryByText(/Run Now/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Scraper Status/i)).not.toBeInTheDocument();
  });

  it("drives the backend batch trigger instead of fake per-source controls", async () => {
    const user = userEvent.setup();

    renderWithProviders(<Targets />);

    await user.click(await screen.findByRole("button", { name: /Run target batch/i }));

    await waitFor(() => {
      expect(scraperMocks.triggerBatch).toHaveBeenCalledTimes(1);
    });

    expect(scraperMocks.triggerBatch).toHaveBeenCalledWith();
    expect(screen.queryByText(/Run Now/i)).not.toBeInTheDocument();
  });
});
