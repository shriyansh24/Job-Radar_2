import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ApplicationModal from "../components/pipeline/ApplicationModal";
import type { Application } from "../api/pipeline";

const historyByApplication: Record<string, unknown[]> = {
  "app-1": [
    {
      id: "hist-1",
      old_status: null,
      new_status: "screening",
      change_source: "system",
      note: "Interview history",
      changed_at: "2026-03-22T10:00:00Z",
    },
  ],
  "app-2": [
    {
      id: "hist-2",
      old_status: "applied",
      new_status: "interviewing",
      change_source: "system",
      note: "Second application history",
      changed_at: "2026-03-22T12:00:00Z",
    },
  ],
  "app-3": [
    {
      id: "hist-3",
      old_status: "saved",
      new_status: "applied",
      change_source: "user",
      note: "Applied history",
      changed_at: "2026-03-22T15:00:00Z",
    },
  ],
};

vi.mock("../api/pipeline", () => ({
  pipelineApi: {
    history: vi.fn((id: string) =>
      Promise.resolve({
        data: historyByApplication[id] ?? [],
      })
    ),
  },
}));

vi.mock("../components/interview/InterviewPrepPanel", () => ({
  default: ({ applicationId }: { applicationId: string }) => (
    <div>Prep Panel {applicationId}</div>
  ),
}));

function makeApplication(
  id: string,
  status: Application["status"]
): Application {
  return {
    id,
    job_id: null,
    company_name: "Acme",
    position_title: `Role ${id}`,
    status,
    source: "manual",
    applied_at: null,
    offer_at: null,
    rejected_at: null,
    follow_up_at: null,
    reminder_at: null,
    notes: null,
    salary_offered: null,
    created_at: "2026-03-22T00:00:00Z",
    updated_at: "2026-03-22T00:00:00Z",
  };
}

describe("ApplicationModal", () => {
  it("resets to history when the selected application changes", async () => {
    const user = userEvent.setup();
    const firstApplication = makeApplication("app-1", "interviewing");
    const secondApplication = makeApplication("app-2", "interviewing");
    const onClose = vi.fn();

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <ApplicationModal open onClose={onClose} application={firstApplication} />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Interview history")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Interview Prep" }));
    expect(screen.getByText("Prep Panel app-1")).toBeInTheDocument();

    rerender(
      <QueryClientProvider client={queryClient}>
        <ApplicationModal open onClose={onClose} application={secondApplication} />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Second application history")).toBeInTheDocument();
    expect(screen.queryByText("Prep Panel app-2")).not.toBeInTheDocument();
  });

  it("resets to history when the prep tab is no longer available", async () => {
    const user = userEvent.setup();
    const interviewingApplication = makeApplication("app-1", "interviewing");
    const appliedApplication = makeApplication("app-3", "applied");
    const onClose = vi.fn();

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <ApplicationModal open onClose={onClose} application={interviewingApplication} />
      </QueryClientProvider>
    );

    expect(await screen.findByText("Interview history")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Interview Prep" }));
    expect(screen.getByText("Prep Panel app-1")).toBeInTheDocument();

    rerender(
      <QueryClientProvider client={queryClient}>
        <ApplicationModal open onClose={onClose} application={appliedApplication} />
      </QueryClientProvider>
    );

    expect(screen.queryByRole("button", { name: "Interview Prep" })).not.toBeInTheDocument();
    expect(screen.queryByText("Prep Panel app-1")).not.toBeInTheDocument();
    expect(await screen.findByText("Applied history")).toBeInTheDocument();
  });
});
