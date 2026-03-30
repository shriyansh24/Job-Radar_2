import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const emailMocks = vi.hoisted(() => ({
  listLogs: vi.fn(),
  processWebhook: vi.fn(),
}));

vi.mock("../../api/email", () => ({
  emailApi: emailMocks,
}));

import Email from "../../pages/Email";

describe("Email page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    emailMocks.listLogs.mockResolvedValue({ data: [] });
  });

  it("renders the inbox signal operator surface", async () => {
    renderWithProviders(<Email />);

    expect(await screen.findByRole("heading", { name: "Email Signals" })).toBeInTheDocument();
    expect(screen.getByText("Signal log")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^process signal$/i })).toBeInTheDocument();
    expect(screen.getByText("Scope")).toBeInTheDocument();
  });
});
