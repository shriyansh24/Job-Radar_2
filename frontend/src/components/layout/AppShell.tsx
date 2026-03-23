import { List, Moon, SignOut, Sun } from "@phosphor-icons/react";
import { useLocation } from "react-router-dom";
import { Outlet } from "react-router-dom";
import { WorkspaceShell } from "../system";
import { useAuthStore } from "../../store/useAuthStore";
import { useUIStore } from "../../store/useUIStore";
import { getWorkspaceRoute } from "../../lib/navigation";
import ScraperLog from "../scraper/ScraperLog";
import NotificationBell from "./NotificationBell";
import Sidebar from "./Sidebar";

export default function AppShell() {
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const theme = useUIStore((s) => s.theme);
  const toggleTheme = useUIStore((s) => s.toggleTheme);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const location = useLocation();
  const currentRoute = getWorkspaceRoute(location.pathname);
  const showScraperLog = currentRoute?.group === "Operations";

  return (
    <WorkspaceShell
      sidebar={<Sidebar />}
      header={
        <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
          <div className="min-w-0 flex items-center gap-3">
            <button
              onClick={toggleSidebar}
              className="inline-flex size-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-border bg-bg-secondary text-text-muted transition-[background-color,color] hover:bg-bg-hover hover:text-text-primary"
              aria-label="Toggle sidebar"
            >
              <List size={18} weight="bold" />
            </button>

            <div className="min-w-0">
              <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">
                {currentRoute?.group ?? "Home"}
              </div>
              <div className="flex items-center gap-2">
                <h1 className="truncate text-sm font-semibold tracking-[-0.02em] text-text-primary sm:text-base">
                  {currentRoute?.label ?? "Command Center"}
                </h1>
                {currentRoute?.description ? (
                  <span className="hidden truncate text-sm text-text-muted md:inline">
                    {currentRoute.description}
                  </span>
                ) : null}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <NotificationBell />

            <button
              onClick={toggleTheme}
              className="inline-flex size-9 items-center justify-center rounded-[var(--radius-md)] border border-border bg-bg-secondary text-text-muted transition-[background-color,color] hover:bg-bg-hover hover:text-text-primary"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun size={16} weight="bold" />
              ) : (
                <Moon size={16} weight="bold" />
              )}
            </button>

            <div className="hidden items-center gap-2 rounded-full border border-border bg-bg-secondary px-3 py-1.5 sm:flex">
              <div className="flex size-6 items-center justify-center rounded-full bg-accent-primary/15 text-[10px] font-bold text-accent-primary">
                {(user?.display_name || user?.email || "U")[0].toUpperCase()}
              </div>
              <span className="max-w-40 truncate text-xs text-text-secondary">
                {user?.display_name || user?.email}
              </span>
            </div>

            <button
              onClick={logout}
              className="inline-flex items-center gap-1.5 rounded-[var(--radius-md)] border border-border bg-bg-secondary px-3 py-2 text-xs text-text-muted transition-[background-color,color] hover:bg-bg-hover hover:text-text-primary"
            >
              <SignOut size={14} weight="bold" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      }
    >
      <div className="min-h-0">
        <Outlet />
      </div>
      {showScraperLog ? <ScraperLog /> : null}
    </WorkspaceShell>
  );
}
