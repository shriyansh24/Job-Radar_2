import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const navigateMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

import Onboarding from "../../pages/Onboarding";

describe("Onboarding page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the first-run setup flow and advances to the profile step", async () => {
    const user = userEvent.setup();

    renderWithProviders(<Onboarding />);

    expect(await screen.findByRole("heading", { name: "Onboarding" })).toBeInTheDocument();
    expect(screen.getByText("What gets configured")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^next$/i }));

    expect(await screen.findByText("Shape the profile")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^back$/i })).toBeInTheDocument();
  });
});
