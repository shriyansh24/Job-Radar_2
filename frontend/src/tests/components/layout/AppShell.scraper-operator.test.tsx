import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes, MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Targets from "../../../pages/Targets";
import { createTestQueryClient } from "../../support/test-utils";

const authMocks = vi.hoisted(() => ({
  state: {
    current: {
      user: { email: "operator@example.com", display_name: "Operator" },
      logout: vi.fn().mockResolvedValue(undefined),
    },
  },
}));

const uiMocks = vi.hoisted(() => ({
  state: {
    current: {
      sidebarCollapsed: false,
      toggleSidebar: vi.fn(),
      mobileNavOpen: false,
      setMobileNavOpen: vi.fn(),
      toggleMobileNav: vi.fn(),
      mode: "dark" as const,
      toggleMode: vi.fn(),
    },
  },
}));

const scraperMocks = vi.hoisted(() => ({
  listTargets: vi.fn(),
  getTarget: vi.fn(),
  triggerBatch: vi.fn(),
  updateTarget: vi.fn(),
  triggerTarget: vi.fn(),
  releaseTarget: vi.fn(),
  importTargets: vi.fn(),
  stream: vi.fn(),
}));

const eventSourceMock = vi.hoisted(() =>
  vi.fn(function EventSourceMock(this: { url: string; close: ReturnType<typeof vi.fn> }, url: string) {
    this.url = url;
    this.close = vi.fn();
  })
);

vi.mock("../../../store/useAuthStore", () => ({
  useAuthStore: (
    selector: (state: typeof authMocks.state.current) => unknown
  ) => selector(authMocks.state.current),
}));

vi.mock("../../../store/useUIStore", () => ({
  useUIStore: (
    selector: (state: typeof uiMocks.state.current) => unknown
  ) => selector(uiMocks.state.current),
}));

vi.mock("../../../components/layout/NotificationBell", () => ({
  default: () => <div data-testid="notification-bell" />,
}));

vi.mock("../../../components/layout/Sidebar", () => ({
  default: () => <aside data-testid="sidebar" />,
}));

vi.mock("../../../api/scraper", () => ({
  scraperApi: scraperMocks,
}));

import AppShell from "../../../components/layout/AppShell";

function renderTargetsRoute() {
  const queryClient = createTestQueryClient();

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/targets"]}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/targets" element={<Targets />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("AppShell scraper operator exposure", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.scrollTo = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "setPointerCapture", {
      value: vi.fn(),
      configurable: true,
      writable: true,
    });
    scraperMocks.listTargets.mockResolvedValue({
      data: {
        items: [
          {
            id: "target-1",
            url: "https://acme.example/jobs",
            company_name: "Acme",
            company_domain: "acme.example",
            source_kind: "career_page",
            ats_vendor: "greenhouse",
            ats_board_token: "acme",
            start_tier: 1,
            max_tier: 3,
            priority_class: "hot",
            schedule_interval_m: 60,
            enabled: true,
            quarantined: false,
            quarantine_reason: null,
            last_success_at: "2026-03-22T12:00:00Z",
            last_failure_at: null,
            last_success_tier: 2,
            last_http_status: 200,
            content_hash: "hash",
            consecutive_failures: 0,
            failure_count: 0,
            next_scheduled_at: "2026-03-24T12:00:00Z",
            lca_filings: 0,
            industry: "Software",
            created_at: "2026-03-01T12:00:00Z",
            updated_at: "2026-03-22T12:00:00Z",
          },
        ],
        total: 1,
      },
    });
    scraperMocks.triggerBatch.mockResolvedValue({
      data: {
        run_id: "run-1",
        targets_attempted: 1,
        targets_succeeded: 1,
        targets_failed: 0,
        jobs_found: 4,
        errors: [],
      },
    });
    scraperMocks.getTarget.mockResolvedValue({ data: null });
    scraperMocks.updateTarget.mockResolvedValue({ data: null });
    scraperMocks.triggerTarget.mockResolvedValue({ data: null });
    scraperMocks.releaseTarget.mockResolvedValue({ data: null });
    scraperMocks.importTargets.mockResolvedValue({
      data: { imported: 0, skipped: 0, errors: [] },
    });
    scraperMocks.stream.mockReturnValue("/api/v1/scraper/stream");
    Object.defineProperty(window, "EventSource", {
      value: eventSourceMock,
      configurable: true,
      writable: true,
    });
    Object.defineProperty(globalThis, "EventSource", {
      value: eventSourceMock,
      configurable: true,
      writable: true,
    });
  });

  it("exposes the scraper log toggle on the targets route", async () => {
    renderTargetsRoute();

    expect(await screen.findByRole("heading", { name: /Scrape Targets/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Scraper Log/i })).toBeInTheDocument();
  });

  it("opens and closes the scraper log without breaking the targets shell", async () => {
    const user = userEvent.setup();

    renderTargetsRoute();

    const toggle = await screen.findByRole("button", { name: /Scraper Log/i });
    await user.click(toggle);

    expect(await screen.findByText(/Live Scraper Log/i)).toBeInTheDocument();
    expect(eventSourceMock).toHaveBeenCalledWith("/api/v1/scraper/stream");
    expect(screen.getByRole("heading", { name: /Scrape Targets/i })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Scraper Log/i }));

    await waitFor(() => {
      expect(screen.queryByText(/Live Scraper Log/i)).not.toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: /Scrape Targets/i })).toBeInTheDocument();

    const instance = eventSourceMock.mock.instances[0] as { close: ReturnType<typeof vi.fn> };
    expect(instance.close).toHaveBeenCalledTimes(1);
  });
});
