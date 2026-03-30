import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const phase7aMocks = vi.hoisted(() => ({
  listCompanies: vi.fn(),
}));

vi.mock("../../api/phase7a", () => ({
  sourceHealthApi: {
    list: vi.fn(),
  },
  companiesApi: {
    list: phase7aMocks.listCompanies,
  },
  searchExpansionApi: {
    expand: vi.fn(),
  },
}));

import Companies from "../../pages/Companies";

describe("Companies page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    phase7aMocks.listCompanies.mockResolvedValue([
      {
        id: "company-1",
        canonical_name: "Acme",
        domain: "acme.example",
        careers_url: null,
        ats_provider: "greenhouse",
        validation_state: "verified",
        confidence_score: 0.91,
        job_count: 12,
        source_count: 3,
        ats_slug: null,
        last_validated_at: null,
      },
    ]);
  });

  it("renders companies data in the companies table", async () => {
    renderWithProviders(<Companies />);

    expect(
      await screen.findByRole("heading", { name: /Companies/i })
    ).toBeInTheDocument();
    expect(await screen.findByText("Acme")).toBeInTheDocument();
    expect(screen.getByText("acme.example")).toBeInTheDocument();
    expect(screen.getByText("91%")).toBeInTheDocument();
  });
});
