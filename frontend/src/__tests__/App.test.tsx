import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../api/auth", () => ({
  getMeApi: vi.fn().mockRejectedValue(new Error("unauthenticated")),
  loginApi: vi.fn(),
  logoutApi: vi.fn(),
  refreshApi: vi.fn().mockRejectedValue(new Error("unauthenticated")),
}));

import App from "../App";

describe("App", () => {
  it("renders login page by default when not authenticated", async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    });
  });
});
