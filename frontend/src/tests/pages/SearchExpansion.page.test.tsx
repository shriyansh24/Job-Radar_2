import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const phase7aMocks = vi.hoisted(() => ({
  expand: vi.fn(),
}));

vi.mock("../../api/phase7a", () => ({
  sourceHealthApi: {
    list: vi.fn(),
  },
  companiesApi: {
    list: vi.fn(),
  },
  searchExpansionApi: {
    expand: phase7aMocks.expand,
  },
}));

import SearchExpansion from "../../pages/SearchExpansion";

describe("Search Expansion page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    phase7aMocks.expand.mockResolvedValue({
      original_query: "react engineer",
      expanded_terms: ["frontend engineer", "ui engineer"],
      synonyms: ["react developer"],
      message: "Query expansion pending LLM integration",
    });
  });

  it("runs search expansion against the live endpoint contract", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SearchExpansion />);

    expect(
      await screen.findByRole("heading", { name: /Search Expansion/i })
    ).toBeInTheDocument();

    await user.clear(screen.getByPlaceholderText("senior frontend engineer"));
    await user.type(
      screen.getByPlaceholderText("senior frontend engineer"),
      "react engineer"
    );
    await user.keyboard("{Enter}");

    expect(phase7aMocks.expand).toHaveBeenCalledWith("react engineer");
    expect(
      await screen.findByText("Query expansion pending LLM integration")
    ).toBeInTheDocument();
    expect(screen.getByText("frontend engineer")).toBeInTheDocument();
    expect(screen.getByText("react developer")).toBeInTheDocument();
  });

  it("stores recent queries and replays them from the sidebar", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SearchExpansion />);

    await user.clear(screen.getByPlaceholderText("senior frontend engineer"));
    await user.type(
      screen.getByPlaceholderText("senior frontend engineer"),
      "react engineer"
    );
    await user.keyboard("{Enter}");

    expect(
      await screen.findByRole("button", { name: /react engineer/i })
    ).toBeInTheDocument();

    phase7aMocks.expand.mockClear();
    await user.click(screen.getByRole("button", { name: /react engineer/i }));

    expect(phase7aMocks.expand).toHaveBeenCalledWith("react engineer");
  });
});
