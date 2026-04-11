import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "../../store/useAuthStore";

// Mock the auth API layer — hoisted before the store is imported
vi.mock("../../api/auth", () => ({
  loginApi: vi.fn(),
  getMeApi: vi.fn(),
  logoutApi: vi.fn(),
  refreshApi: vi.fn(),
}));

import * as authApi from "../../api/auth";

const mockLoginApi = vi.mocked(authApi.loginApi);
const mockGetMeApi = vi.mocked(authApi.getMeApi);
const mockLogoutApi = vi.mocked(authApi.logoutApi);
const mockRefreshApi = vi.mocked(authApi.refreshApi);

const MOCK_USER = { id: "user-1", email: "alice@example.com" } as const;

beforeEach(() => {
  vi.clearAllMocks();
  // Reset store to pristine state
  useAuthStore.setState({ user: null, isAuthenticated: false, initialized: false });
});

describe("useAuthStore – login", () => {
  it("sets isAuthenticated and user on success", async () => {
    mockLoginApi.mockResolvedValue(undefined as never);
    mockGetMeApi.mockResolvedValue(MOCK_USER as never);

    await useAuthStore.getState().login("alice@example.com", "password");

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(MOCK_USER);
    expect(state.initialized).toBe(true);
  });

  it("calls loginApi then getMeApi in order", async () => {
    mockLoginApi.mockResolvedValue(undefined as never);
    mockGetMeApi.mockResolvedValue(MOCK_USER as never);

    await useAuthStore.getState().login("alice@example.com", "pass");

    expect(mockLoginApi).toHaveBeenCalledWith("alice@example.com", "pass");
    expect(mockGetMeApi).toHaveBeenCalledTimes(1);
  });

  it("throws when loginApi rejects", async () => {
    mockLoginApi.mockRejectedValue(new Error("Unauthorized"));

    await expect(useAuthStore.getState().login("bad@example.com", "wrong")).rejects.toThrow();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});

describe("useAuthStore – logout", () => {
  it("clears user and isAuthenticated after logout", async () => {
    useAuthStore.setState({ user: MOCK_USER as never, isAuthenticated: true, initialized: true });
    mockLogoutApi.mockResolvedValue(undefined as never);

    await useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.initialized).toBe(true);
  });

  it("clears state even when logoutApi throws", async () => {
    useAuthStore.setState({ user: MOCK_USER as never, isAuthenticated: true, initialized: true });
    mockLogoutApi.mockRejectedValue(new Error("Network error"));

    // The store uses finally so state is cleared even though the error propagates
    try {
      await useAuthStore.getState().logout();
    } catch {
      // expected — logoutApi threw, state should still be cleared
    }

    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});

describe("useAuthStore – refresh", () => {
  it("sets user on successful refresh", async () => {
    mockRefreshApi.mockResolvedValue(undefined as never);
    mockGetMeApi.mockResolvedValue(MOCK_USER as never);

    await useAuthStore.getState().refresh();

    const state = useAuthStore.getState();
    expect(state.user).toEqual(MOCK_USER);
    expect(state.isAuthenticated).toBe(true);
    expect(state.initialized).toBe(true);
  });

  it("sets isAuthenticated=false when refresh fails", async () => {
    mockRefreshApi.mockRejectedValue(new Error("Refresh failed"));

    await useAuthStore.getState().refresh();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.initialized).toBe(true);
  });
});

describe("useAuthStore – loadFromSession", () => {
  it("sets user if getMeApi succeeds on cold boot", async () => {
    mockGetMeApi.mockResolvedValue(MOCK_USER as never);

    await useAuthStore.getState().loadFromSession();

    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().user).toEqual(MOCK_USER);
    expect(useAuthStore.getState().initialized).toBe(true);
  });

  it("tries refresh when getMeApi fails, then populates user", async () => {
    mockGetMeApi
      .mockRejectedValueOnce(new Error("No cookie")) // first call fails
      .mockResolvedValueOnce(MOCK_USER as never);     // second call succeeds
    mockRefreshApi.mockResolvedValue(undefined as never);

    await useAuthStore.getState().loadFromSession();

    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(mockRefreshApi).toHaveBeenCalledTimes(1);
  });

  it("sets initialized=true with null user when both getMeApi and refresh fail", async () => {
    mockGetMeApi.mockRejectedValue(new Error("No cookie"));
    mockRefreshApi.mockRejectedValue(new Error("Refresh failed"));

    await useAuthStore.getState().loadFromSession();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.initialized).toBe(true);
  });
});
