import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import JobDetail from "../components/jobs/JobDetail";
import { renderWithProviders } from "./testUtils";

const pipelineMocks = vi.hoisted(() => ({
  create: vi.fn(),
}));

vi.mock("../api/pipeline", () => ({
  pipelineApi: pipelineMocks,
}));

const baseJob = {
  id: "job-1",
  source: "greenhouse",
  source_url: "https://acme.example/jobs/1",
  title: "Backend Engineer",
  company_name: "Acme",
  company_domain: "acme.example",
  company_logo_url: null,
  location: "Remote",
  location_city: null,
  location_state: null,
  location_country: null,
  remote_type: "remote",
  description_markdown: "Test description",
  summary_ai: null,
  skills_required: [],
  skills_nice_to_have: [],
  tech_stack: [],
  red_flags: [],
  green_flags: [],
  match_score: null,
  tfidf_score: null,
  salary_min: null,
  salary_max: null,
  salary_period: null,
  salary_currency: "USD",
  experience_level: null,
  job_type: null,
  status: "new",
  is_starred: false,
  is_enriched: false,
  is_hidden: false,
  posted_at: null,
  scraped_at: "2026-03-22T12:00:00Z",
  created_at: "2026-03-22T12:00:00Z",
};

describe("JobDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    pipelineMocks.create.mockResolvedValue({ data: null });
    window.open = vi.fn();
  });

  it("hides the original-link action for unsafe source urls", () => {
    renderWithProviders(
      <JobDetail
        job={{ ...baseJob, source_url: "javascript:alert(1)" }}
        onClose={vi.fn()}
      />
    );

    expect(screen.queryByRole("button", { name: /Original/i })).not.toBeInTheDocument();
  });

  it("opens safe source urls with opener protections", async () => {
    const user = userEvent.setup();

    renderWithProviders(<JobDetail job={baseJob} onClose={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /Original/i }));

    expect(window.open).toHaveBeenCalledWith(
      "https://acme.example/jobs/1",
      "_blank",
      "noopener,noreferrer"
    );
  });
});
