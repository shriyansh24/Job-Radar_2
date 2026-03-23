import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./testUtils";

const salaryMocks = vi.hoisted(() => ({
  research: vi.fn(),
  evaluateOffer: vi.fn(),
}));

vi.mock("../api/salary", () => ({
  salaryApi: salaryMocks,
}));

import SalaryInsights from "../pages/SalaryInsights";

describe("SalaryInsights page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    salaryMocks.research.mockResolvedValue({
      data: {
        min_salary: 120000,
        percentile_25: 150000,
        median_salary: 180000,
        percentile_75: 205000,
        max_salary: 230000,
        currency: "USD",
        data_sources: ["levels.fyi"],
      },
    });
    salaryMocks.evaluateOffer.mockResolvedValue({ data: null });
  });

  it("renders the research flow and displays returned salary data", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SalaryInsights />);

    expect(
      await screen.findByRole("heading", { name: /Salary Insights/i })
    ).toBeInTheDocument();

    await user.type(
      screen.getByPlaceholderText("e.g. Senior Software Engineer"),
      "Staff Engineer"
    );
    await user.click(screen.getByRole("button", { name: /^Research$/i }));

    expect(await screen.findByText("Salary Range")).toBeInTheDocument();
    expect(screen.getByText("Based on 1 sources (USD)")).toBeInTheDocument();
    expect(screen.getAllByText("$180k").length).toBeGreaterThan(0);
    expect(screen.getByText("Recent Research")).toBeInTheDocument();
    expect(screen.getByText("Staff Engineer")).toBeInTheDocument();
  });
});
