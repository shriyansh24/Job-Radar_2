import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/test-utils";

const phase7aMocks = vi.hoisted(() => ({
  listSourceHealth: vi.fn(),
  listCompanies: vi.fn(),
  expand: vi.fn(),
}));

vi.mock("../../api/phase7a", () => ({
  sourceHealthApi: {
    list: phase7aMocks.listSourceHealth,
  },
  companiesApi: {
    list: phase7aMocks.listCompanies,
  },
  searchExpansionApi: {
    expand: phase7aMocks.expand,
  },
}));

import Companies from "../../pages/Companies";
import SearchExpansion from "../../pages/SearchExpansion";
import Sources from "../../pages/Sources";

describe("Operations pages contracts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    phase7aMocks.listSourceHealth.mockResolvedValue([
      {
        id: "source-1",
        source_name: "LinkedIn",
        health_state: "healthy",
        quality_score: 0.84,
        total_jobs_found: 120,
        last_check_at: "2026-03-22T12:00:00Z",
        failure_count: 1,
        backoff_until: null,
        created_at: "2026-03-20T12:00:00Z",
      },
    ]);
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
    phase7aMocks.expand.mockResolvedValue({
      original_query: "react engineer",
      expanded_terms: ["frontend engineer", "ui engineer"],
      synonyms: ["react developer"],
      message: "Query expansion pending LLM integration",
    });
  });

  it("renders source health cards from query data", async () => {
    renderWithProviders(<Sources />);

    expect(
      await screen.findByRole("heading", { name: /Source Health/i })
    ).toBeInTheDocument();
    expect(await screen.findByText("LinkedIn")).toBeInTheDocument();
    expect(screen.getByText("84%")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
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

  it("runs search expansion against the live endpoint contract", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SearchExpansion />);

    expect(
      await screen.findByRole("heading", { name: /Search Expansion/i })
    ).toBeInTheDocument();

    await user.clear(screen.getByPlaceholderText("senior frontend engineer"));
    await user.type(screen.getByPlaceholderText("senior frontend engineer"), "react engineer");
    await user.keyboard("{Enter}");

    expect(phase7aMocks.expand).toHaveBeenCalledWith("react engineer");
    expect(await screen.findByText("Query expansion pending LLM integration")).toBeInTheDocument();
    expect(screen.getByText("frontend engineer")).toBeInTheDocument();
    expect(screen.getByText("react developer")).toBeInTheDocument();
  });
});
