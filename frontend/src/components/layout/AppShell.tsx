import { List, Moon, SignOut, Sun, UserCircle } from "@phosphor-icons/react";
import { Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/useAuthStore";
import { useUIStore } from "../../store/useUIStore";
import ScraperLog from "../scraper/ScraperLog";
import NotificationBell from "./NotificationBell";
import Sidebar from "./Sidebar";

export default function AppShell() {
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const theme = useUIStore((s) => s.theme);
  const toggleTheme = useUIStore((s) => s.toggleTheme);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="flex min-h-[100dvh] bg-bg-primary">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-border bg-bg-secondary/80 supports-[backdrop-filter]:bg-bg-secondary/70 backdrop-blur flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <button
              onClick={toggleSidebar}
              className="p-2 rounded-[var(--radius-md)] hover:bg-bg-tertiary text-text-secondary transition-[background-color,color] duration-[var(--transition-fast)]"
              aria-label="Toggle sidebar"
            >
              <List size={20} weight="bold" />
            </button>

            <div className="hidden md:flex items-center gap-2 px-2 py-1 rounded-[var(--radius-md)] border border-border bg-bg-secondary">
              <span className="text-xs text-text-muted tracking-tight">
                JobRadar
              </span>
              <span className="text-xs font-mono text-text-secondary">
                v2
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <NotificationBell />

            <button
              onClick={toggleTheme}
              className="p-2 rounded-[var(--radius-md)] hover:bg-bg-tertiary text-text-secondary transition-[background-color,color] duration-[var(--transition-fast)]"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun size={18} weight="bold" />
              ) : (
                <Moon size={18} weight="bold" />
              )}
            </button>

            <div className="hidden sm:flex items-center gap-2 px-2 py-1.5 rounded-[var(--radius-md)] border border-border bg-bg-secondary">
              <UserCircle size={18} weight="fill" className="text-text-muted" />
              <span className="text-sm text-text-secondary">
                {user?.display_name || user?.email}
              </span>
            </div>

            <button
              onClick={logout}
              className="flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius-md)] text-sm text-text-secondary hover:bg-bg-tertiary transition-[background-color,color,transform] duration-[var(--transition-fast)] active:translate-y-[1px]"
            >
              <SignOut size={16} weight="bold" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
      <ScraperLog />
    </div>
  );
}
