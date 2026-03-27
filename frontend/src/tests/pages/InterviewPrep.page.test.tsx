import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/test-utils";

const interviewMocks = vi.hoisted(() => ({
  listSessions: vi.fn(),
  generate: vi.fn(),
  getSession: vi.fn(),
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
});
