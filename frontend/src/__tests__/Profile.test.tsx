import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./testUtils";

const profileMocks = vi.hoisted(() => ({
  get: vi.fn(),
  update: vi.fn(),
  generateAnswers: vi.fn(),
}));

vi.mock("../api/profile", () => ({
  profileApi: profileMocks,
}));

vi.mock("../store/useAuthStore", () => ({
  useAuthStore: (
    selector: (state: { user: { email: string } | null }) => unknown
  ) => selector({ user: { email: "jane@example.com" } }),
}));

import Profile from "../pages/Profile";

describe("Profile page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    profileMocks.get.mockResolvedValue({
      data: {
        full_name: "Jane Doe",
        phone: "+1 555 0100",
        location: "Chicago, IL",
        linkedin_url: "https://linkedin.com/in/janedoe",
        github_url: "https://github.com/janedoe",
        portfolio_url: "https://janedoe.dev",
        work_authorization: "citizen",
        preferred_job_types: ["full_time"],
        preferred_remote_types: ["remote"],
        salary_min: 160000,
        salary_max: 210000,
        education: [],
        work_experience: [],
        search_queries: ["Senior React Engineer"],
        search_locations: ["Chicago, IL"],
        watchlist_companies: ["Acme"],
        answer_bank: {
          "Tell me about yourself": "I build frontend systems.",
        },
      },
    });
    profileMocks.update.mockResolvedValue({ data: null });
    profileMocks.generateAnswers.mockResolvedValue({ data: null });
  });

  it("renders profile data loaded from the API", async () => {
    renderWithProviders(<Profile />);

    expect(
      await screen.findByRole("heading", { name: "Profile" })
    ).toBeInTheDocument();
    expect(await screen.findByDisplayValue("Jane Doe")).toBeInTheDocument();
    expect(screen.getByDisplayValue("jane@example.com")).toBeInTheDocument();
    expect(screen.getByText("Senior React Engineer")).toBeInTheDocument();
    expect(screen.getByText("Acme")).toBeInTheDocument();
    expect(screen.getByText("Tell me about yourself")).toBeInTheDocument();
  });
});
