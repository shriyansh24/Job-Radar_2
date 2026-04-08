import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Login from "../../pages/Login";

// Mock auth store login action
const mockLogin = vi.fn();
vi.mock("../../store/useAuthStore", () => ({
  useAuthStore: (selector: (s: { login: typeof mockLogin }) => unknown) =>
    selector({ login: mockLogin }),
}));

// Mock UI store (theme only)
vi.mock("../../store/useUIStore", () => ({
  useUIStore: () => ({ theme: "light", toggleTheme: vi.fn() }),
}));

// Mock router navigation
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => mockNavigate };
});

function renderLogin() {
  return render(
    <BrowserRouter>
      <Login />
    </BrowserRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Login", () => {
  it("renders login form", () => {
    renderLogin();
    expect(screen.getByRole("heading", { name: /^sign in$/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("you@example.com")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  });

  it("calls loginApi with email and password on submit", async () => {
    mockLogin.mockResolvedValue(undefined);
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "alice@example.com");
    await userEvent.type(screen.getByPlaceholderText("Enter password"), "secret");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("alice@example.com", "secret");
    });
  });

  it("navigates to / after successful login", async () => {
    mockLogin.mockResolvedValue(undefined);
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "alice@example.com");
    await userEvent.type(screen.getByPlaceholderText("Enter password"), "password");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/", { replace: true });
    });
  });

  it("shows error message when login fails", async () => {
    mockLogin.mockRejectedValue(new Error("Unauthorized"));
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "wrong@example.com");
    await userEvent.type(screen.getByPlaceholderText("Enter password"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument();
    });
  });

  it("shows network error message when backend is unreachable", async () => {
    mockLogin.mockRejectedValue(new Error("Network Error"));
    renderLogin();

    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "user@example.com");
    await userEvent.type(screen.getByPlaceholderText("Enter password"), "pass");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText(/unable to reach the backend/i)).toBeInTheDocument();
    });
  });

  it("submit button shows loading state during login", async () => {
    let resolveLogin: () => void;
    mockLogin.mockReturnValue(
      new Promise<void>((resolve) => {
        resolveLogin = resolve;
      })
    );

    renderLogin();
    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "alice@example.com");
    await userEvent.type(screen.getByPlaceholderText("Enter password"), "secret");

    const submitBtn = screen.getByRole("button", { name: "Sign in" });
    await userEvent.click(submitBtn);

    // Button should be disabled while loading
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Sign in" })).toBeDisabled();
    });

    resolveLogin!();
  });

  it("keeps session checkbox is checked by default", () => {
    renderLogin();
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeChecked();
  });

  it("can uncheck the keep session checkbox", async () => {
    renderLogin();
    const checkbox = screen.getByRole("checkbox");
    await userEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });
});

