import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const copilotMocks = vi.hoisted(() => ({
  chat: vi.fn(),
  askHistory: vi.fn(),
  generateCoverLetter: vi.fn(),
}));

const jobsMocks = vi.hoisted(() => ({
  list: vi.fn(),
}));

vi.mock("../../api/copilot", () => ({
  copilotApi: copilotMocks,
}));

vi.mock("../../api/jobs", () => ({
  jobsApi: jobsMocks,
}));

import Copilot from "../../pages/Copilot";

describe("Copilot page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    jobsMocks.list.mockResolvedValue({
      data: {
        items: [{ id: "job-1", title: "Platform Engineer", company_name: "Acme" }],
      },
    });
  });

  it("renders chat, history, and letter tabs with live job context", async () => {
    renderWithProviders(<Copilot />);

    expect(await screen.findByRole("heading", { name: "Copilot" })).toBeInTheDocument();
    expect(screen.getByText("Switch tasks")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^assistant$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^history$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^letters$/i })).toBeInTheDocument();
  });
});
