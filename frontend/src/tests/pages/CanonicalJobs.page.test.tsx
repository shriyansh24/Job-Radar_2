import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const canonicalJobsMocks = vi.hoisted(() => ({
  list: vi.fn(),
  close: vi.fn(),
  reactivate: vi.fn(),
}));

vi.mock("../../api/phase7a", async () => {
  const actual = await vi.importActual<typeof import("../../api/phase7a")>("../../api/phase7a");
  return {
    ...actual,
    canonicalJobsApi: canonicalJobsMocks,
  };
});

import CanonicalJobs from "../../pages/CanonicalJobs";

describe("CanonicalJobs page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    canonicalJobsMocks.list.mockResolvedValue([
      {
        id: "canon-1",
        title: "Platform Engineer",
        company_name: "Acme",
        company_domain: "acme.example",
        location: "Remote",
        remote_type: "remote",
        status: "open",
        source_count: 2,
        first_seen_at: "2026-03-20T00:00:00Z",
        last_refreshed_at: "2026-03-26T00:00:00Z",
        is_stale: false,
        merged_data: null,
        created_at: "2026-03-20T00:00:00Z",
      },
    ]);
  });

  it("renders canonical job rows and stale-toggle controls", async () => {
    renderWithProviders(<CanonicalJobs />);

    expect(await screen.findByRole("heading", { name: "Canonical Jobs" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /show stale/i })).toBeInTheDocument();
    expect(await screen.findByText("Platform Engineer")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /^close$/i })).toBeInTheDocument();
  });
});
