import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/test-utils";

const salaryMocks = vi.hoisted(() => ({
  research: vi.fn(),
  evaluateOffer: vi.fn(),
}));

vi.mock("../../api/salary", () => ({
  salaryApi: salaryMocks,
}));

import SalaryInsights from "../../pages/SalaryInsights";

describe("SalaryInsights page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    salaryMocks.research.mockResolvedValue({
      data: {
        job_title: "Staff Engineer",
        location: null,
        p25: 150000,
        p50: 180000,
        p75: 205000,
        p90: 230000,
        currency: "USD",
        yoe_brackets: [{ years: "5-7", range: "$170k-$210k" }],
        competing_companies: ["Acme"],
        cached: false,
      },
    });
    salaryMocks.evaluateOffer.mockResolvedValue({
      data: {
        assessment: "Above market for this role and location.",
        counter_offer: 205000,
        walkaway_point: 185000,
        talking_points: ["Use market data", "Anchor on the median"],
        negotiation_script: "I am excited about the role and would like to discuss compensation.",
      },
    });
  });

  it("renders the research flow and displays returned salary data", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SalaryInsights />);

    expect(await screen.findByRole("heading", { name: "Salary Insights" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Senior Frontend Engineer")).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("Senior Frontend Engineer"), "Staff Engineer");
    await user.click(screen.getByRole("button", { name: /^research$/i }));

    expect(await screen.findByText("Range view")).toBeInTheDocument();
    expect(screen.getByText(/Backend percentiles returned in USD/i)).toBeInTheDocument();
    expect(screen.getAllByText("$180k").length).toBeGreaterThan(0);
    expect(screen.getAllByText("General market snapshot").length).toBeGreaterThan(0);

    await user.type(screen.getByPlaceholderText("150000"), "195000");
    await user.click(screen.getByRole("button", { name: /^evaluate$/i }));

    expect(await screen.findByText("Negotiation guidance")).toBeInTheDocument();
    expect(screen.getAllByText("$205k").length).toBeGreaterThan(0);
    expect(screen.getByText(/would like to discuss compensation/i)).toBeInTheDocument();
  });
});
