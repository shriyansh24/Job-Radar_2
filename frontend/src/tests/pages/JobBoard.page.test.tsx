import { screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const jobsMocks = vi.hoisted(() => ({
  list: vi.fn(),
  get: vi.fn(),
  semanticSearch: vi.fn(),
}));

vi.mock("../../api/jobs", () => ({
  jobsApi: jobsMocks,
}));

import JobBoard from "../../pages/JobBoard";

describe("JobBoard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    jobsMocks.list.mockResolvedValue({ data: { items: [], total: 0, total_pages: 0 } });
    jobsMocks.get.mockResolvedValue({ data: null });
    jobsMocks.semanticSearch.mockResolvedValue({ data: [] });
  });

  it("renders the redesigned jobs workspace and empty state", async () => {
    renderWithProviders(<JobBoard />);

    expect(await screen.findByRole("heading", { name: "Jobs" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /exact/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /semantic/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search jobs")).toBeInTheDocument();
    expect(await screen.findByText("No jobs found")).toBeInTheDocument();
    expect(screen.getByText("Adjust the filters or search query.")).toBeInTheDocument();
  });
});
