import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const authGuardMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  state: {
    current: {
      isAuthenticated: false,
      initialized: false,
      loadFromSession: vi.fn<() => Promise<void>>(),
    },
  },
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom"
  );

  return {
    ...actual,
    useNavigate: () => authGuardMocks.navigate,
  };
});

vi.mock("../../../store/useAuthStore", () => ({
  useAuthStore: (
    selector: (state: typeof authGuardMocks.state.current) => unknown
  ) => selector(authGuardMocks.state.current),
}));

import AuthGuard from "../../../components/layout/AuthGuard";

function renderGuard(children: ReactNode = <div>Secret Panel</div>) {
  return render(<AuthGuard>{children}</AuthGuard>);
}

describe("AuthGuard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authGuardMocks.state.current = {
      isAuthenticated: false,
      initialized: false,
      loadFromSession: vi.fn().mockResolvedValue(undefined),
    };
  });

  it("loads session state before rendering protected content", async () => {
    renderGuard();

    await waitFor(() => {
      expect(authGuardMocks.state.current.loadFromSession).toHaveBeenCalledTimes(
        1
      );
    });

    expect(screen.queryByText("Secret Panel")).not.toBeInTheDocument();
    expect(authGuardMocks.navigate).not.toHaveBeenCalled();
  });

  it("renders children for initialized authenticated users", () => {
    authGuardMocks.state.current = {
      isAuthenticated: true,
      initialized: true,
      loadFromSession: vi.fn().mockResolvedValue(undefined),
    };

    renderGuard();

    expect(screen.getByText("Secret Panel")).toBeInTheDocument();
    expect(authGuardMocks.state.current.loadFromSession).not.toHaveBeenCalled();
    expect(authGuardMocks.navigate).not.toHaveBeenCalled();
  });

  it("redirects initialized unauthenticated users to login", async () => {
    authGuardMocks.state.current = {
      isAuthenticated: false,
      initialized: true,
      loadFromSession: vi.fn().mockResolvedValue(undefined),
    };

    renderGuard();

    await waitFor(() => {
      expect(authGuardMocks.navigate).toHaveBeenCalledWith("/login", {
        replace: true,
      });
    });

    expect(screen.queryByText("Secret Panel")).not.toBeInTheDocument();
    expect(authGuardMocks.state.current.loadFromSession).not.toHaveBeenCalled();
  });
});
