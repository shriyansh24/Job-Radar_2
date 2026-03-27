import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../../support/test-utils";

const scraperMocks = vi.hoisted(() => ({
  listTargets: vi.fn(),
  getTarget: vi.fn(),
  triggerBatch: vi.fn(),
  updateTarget: vi.fn(),
  triggerTarget: vi.fn(),
  releaseTarget: vi.fn(),
  importTargets: vi.fn(),
}));

vi.mock("../../../api/scraper", () => ({
  scraperApi: scraperMocks,
}));

import Targets from "../../../pages/Targets";

const defaultTargetDetail = {
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
  quarantined: true,
  quarantine_reason: "manual review required",
  last_success_at: "2026-03-22T12:00:00Z",
  last_failure_at: "2026-03-21T12:00:00Z",
  last_success_tier: 2,
  last_http_status: 200,
  content_hash: "hash",
  consecutive_failures: 1,
  failure_count: 2,
  next_scheduled_at: "2026-03-24T12:00:00Z",
  lca_filings: 0,
  industry: "Software",
  created_at: "2026-03-01T12:00:00Z",
  updated_at: "2026-03-22T12:00:00Z",
  recent_attempts: [
    {
      id: "attempt-1",
      run_id: "run-1",
      target_id: "target-1",
      selected_tier: 1,
      actual_tier_used: 2,
      scraper_name: "scraper",
      parser_name: "parser",
      status: "success",
      http_status: 200,
      duration_ms: 1800,
      retries: 0,
      escalations: 0,
      jobs_extracted: 4,
      content_changed: true,
      error_class: null,
      error_message: null,
      browser_used: false,
      created_at: "2026-03-22T12:00:00Z",
    },
  ],
};

describe("Targets page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.scrollTo = vi.fn();
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
            quarantined: true,
            quarantine_reason: "manual review required",
            last_success_at: "2026-03-22T12:00:00Z",
            last_failure_at: "2026-03-21T12:00:00Z",
            last_success_tier: 2,
            last_http_status: 200,
            content_hash: "hash",
            consecutive_failures: 1,
            failure_count: 2,
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
    scraperMocks.getTarget.mockResolvedValue({
      data: defaultTargetDetail,
    });
    scraperMocks.triggerBatch.mockResolvedValue({ data: { jobs_found: 0 } });
    scraperMocks.updateTarget.mockResolvedValue({ data: null });
    scraperMocks.triggerTarget.mockResolvedValue({ data: null });
    scraperMocks.releaseTarget.mockResolvedValue({ data: null });
    scraperMocks.importTargets.mockResolvedValue({
      data: { imported: 0, skipped: 0, errors: [] },
    });
  });

  it("renders targets and loads detail data when a target is selected", async () => {
    const user = userEvent.setup();

    renderWithProviders(<Targets />);

    expect(await screen.findByText(/Scrape Targets/i)).toBeInTheDocument();
    expect(await screen.findByText("Acme")).toBeInTheDocument();
    expect(screen.getByText("https://acme.example/jobs")).toBeInTheDocument();

    await user.click(screen.getByText("Acme"));

    expect(await screen.findByText("Target Detail")).toBeInTheDocument();
    expect(screen.getByText("manual review required")).toBeInTheDocument();
    expect(screen.getByText("career_page")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Trigger Now/i })).toBeInTheDocument();
  });

  it("does not render unsafe target urls as clickable links", async () => {
    const user = userEvent.setup();
    scraperMocks.getTarget.mockResolvedValueOnce({
      data: {
        ...defaultTargetDetail,
        url: "javascript:alert(1)",
        quarantined: false,
        quarantine_reason: null,
        recent_attempts: [],
      },
    });

    renderWithProviders(<Targets />);
    await user.click(await screen.findByText("Acme"));

    expect(await screen.findByText("javascript:alert(1)")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "javascript:alert(1)" })).not.toBeInTheDocument();
  });

  it("rejects unsafe import urls during preview", async () => {
    const user = userEvent.setup();

    renderWithProviders(<Targets />);
    await user.click(await screen.findByRole("button", { name: /Import Targets/i }));
    fireEvent.change(screen.getByPlaceholderText(/\[\{"url": "https:\/\/\.\.\."/i), {
      target: {
        value: '[{"url":"javascript:alert(1)","company_name":"Acme"}]',
      },
    });
    await user.click(screen.getByRole("button", { name: /Preview/i }));

    expect(
      await screen.findByText(/Each entry must have a valid "http:\/\/" or "https:\/\/" URL/i)
    ).toBeInTheDocument();
  });
});
