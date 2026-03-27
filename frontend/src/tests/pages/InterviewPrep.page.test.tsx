import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const interviewMocks = vi.hoisted(() => ({
  listSessions: vi.fn(),
  generate: vi.fn(),
  getSession: vi.fn(),
  prepare: vi.fn(),
  evaluate: vi.fn(),
}));

const jobsMocks = vi.hoisted(() => ({
  list: vi.fn(),
}));

vi.mock("../../api/interview", () => ({
  interviewApi: interviewMocks,
}));

vi.mock("../../api/jobs", () => ({
  jobsApi: jobsMocks,
}));

import InterviewPrep from "../../pages/InterviewPrep";

describe("InterviewPrep page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    jobsMocks.list.mockResolvedValue({
      data: {
        items: [
          {
            id: "job-1",
            title: "Platform Engineer",
            company_name: "Acme",
          },
        ],
      },
    });
    interviewMocks.listSessions.mockResolvedValue({
      data: [
        {
          id: "abcdefgh1234",
          created_at: "2026-03-22T12:00:00Z",
          overall_score: 8.2,
          scores: [],
          questions: [
            {
              question: "Tell me about a time you improved a system.",
              category: "behavioral",
              difficulty: "medium",
            },
          ],
        },
      ],
    });
    interviewMocks.generate.mockResolvedValue({ data: null });
    interviewMocks.getSession.mockResolvedValue({ data: null });
    interviewMocks.prepare.mockResolvedValue({
      data: {
        likely_questions: [
          {
            question: "How would you stabilize a noisy ingestion pipeline?",
            category: "technical",
          },
        ],
        star_stories: [],
        technical_topics: ["Observability"],
        company_talking_points: [],
        questions_to_ask: [],
        red_flag_responses: [],
        company_research: {
          overview: "Acme builds workflow software.",
          recent_news: ["Shipped a new platform"],
          culture_values: ["Ownership"],
          interview_style: "Structured loop",
        },
        role_analysis: {
          key_requirements: ["Python"],
          skill_gaps: ["None"],
          talking_points: ["Scaled systems"],
          seniority_expectations: "Senior IC",
        },
      },
    });
    interviewMocks.evaluate.mockResolvedValue({ data: null });
  });

  it("renders practice state and shows session history when the history tab is selected", async () => {
    const user = userEvent.setup();

    renderWithProviders(<InterviewPrep />);

    expect(
      await screen.findByRole("heading", { name: /Interview Prep/i })
    ).toBeInTheDocument();
    expect(screen.getByText("No active session")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /History/i }));

    expect(await screen.findByText(/Session abcdefgh/i)).toBeInTheDocument();
    expect(screen.getByText("1 questions")).toBeInTheDocument();
    expect(screen.getByText("behavioral")).toBeInTheDocument();
  });

  it("generates a prep bundle from the prepare tab", async () => {
    const user = userEvent.setup();

    renderWithProviders(<InterviewPrep />);

    expect(await screen.findByRole("heading", { name: /Interview Prep/i })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Prepare/i }));
    await user.selectOptions(screen.getByLabelText("Target job"), "job-1");
    await user.selectOptions(screen.getByLabelText("Interview stage"), "technical");
    await user.type(
      screen.getByLabelText("Resume text"),
      "Experienced backend engineer with Python, FastAPI, PostgreSQL, and observability work across scraping and workflow systems."
    );
    await user.click(screen.getByRole("button", { name: /Generate bundle/i }));

    expect(interviewMocks.prepare).toHaveBeenCalledWith(
      expect.objectContaining({
        job_id: "job-1",
        stage: "technical",
      }),
      expect.anything()
    );
    expect(await screen.findByText("Company research")).toBeInTheDocument();
    expect(screen.getByText(/Acme builds workflow software/i)).toBeInTheDocument();
    expect(screen.getByText(/How would you stabilize a noisy ingestion pipeline/i)).toBeInTheDocument();
  });
});
