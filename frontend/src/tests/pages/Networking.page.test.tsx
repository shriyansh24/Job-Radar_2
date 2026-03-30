import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const jobsMocks = vi.hoisted(() => ({
  list: vi.fn(),
}));

const networkingMocks = vi.hoisted(() => ({
  listContacts: vi.fn(),
  listReferralRequests: vi.fn(),
  createContact: vi.fn(),
  updateContact: vi.fn(),
  deleteContact: vi.fn(),
  findConnections: vi.fn(),
  suggestReferrals: vi.fn(),
  generateOutreach: vi.fn(),
  createReferralRequest: vi.fn(),
}));

vi.mock("../../api/jobs", () => ({
  jobsApi: jobsMocks,
}));

vi.mock("../../api/networking", () => ({
  networkingApi: networkingMocks,
}));

import Networking from "../../pages/Networking";

describe("Networking page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    jobsMocks.list.mockResolvedValue({
      data: {
        items: [{ id: "job-1", title: "Platform Engineer", company_name: "Acme" }],
      },
    });
    networkingMocks.listContacts.mockResolvedValue({ data: [] });
    networkingMocks.listReferralRequests.mockResolvedValue({ data: [] });
  });

  it("renders the networking operator surface for a fresh account", async () => {
    renderWithProviders(<Networking />);

    expect(await screen.findByRole("heading", { name: "Networking" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^new contact$/i })).toBeInTheDocument();
    expect(screen.getAllByText("Contacts").length).toBeGreaterThan(0);
    expect(screen.getByText("Referral queue")).toBeInTheDocument();
    expect(screen.getByText("No referral requests yet")).toBeInTheDocument();
  });
});
