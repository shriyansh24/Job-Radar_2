import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./testUtils";

const phase7aMocks = vi.hoisted(() => ({
  listSourceHealth: vi.fn(),
  listCompanies: vi.fn(),
  listTemplates: vi.fn(),
}));

vi.mock("../api/phase7a", () => ({
  sourceHealthApi: {
    list: phase7aMocks.listSourceHealth,
  },
  companiesApi: {
    list: phase7aMocks.listCompanies,
  },
  searchExpansionApi: {
    listTemplates: phase7aMocks.listTemplates,
  },
}));

import Companies from "../pages/Companies";
import SearchExpansion from "../pages/SearchExpansion";
import Sources from "../pages/Sources";

describe("Phase 7A pages", () => {
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
        source_type: "scraper",
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
    phase7aMocks.listTemplates.mockResolvedValue([
      {
        id: "template-1",
        name: "React Roles",
        base_query: "react engineer",
        expanded_queries: ["frontend engineer", "ui engineer"],
        strictness: "balanced",
        is_active: true,
        created_at: "2026-03-22T12:00:00Z",
      },
    ]);
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

  it("renders search templates and expanded queries", async () => {
    renderWithProviders(<SearchExpansion />);

    expect(
      await screen.findByRole("heading", { name: /Search Expansion/i })
    ).toBeInTheDocument();
    expect(await screen.findByText("React Roles")).toBeInTheDocument();
    expect(screen.getByText("react engineer")).toBeInTheDocument();
    expect(screen.getByText("frontend engineer")).toBeInTheDocument();
  });
});
