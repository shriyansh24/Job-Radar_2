import { List, Moon, SignOut, Sun } from "@phosphor-icons/react";
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
        <header className="h-12 border-b border-border bg-bg-secondary/80 supports-[backdrop-filter]:bg-bg-secondary/60 backdrop-blur-xl flex items-center justify-between px-3">
          <div className="flex items-center gap-1.5">
            <button
              onClick={toggleSidebar}
              className="p-1.5 rounded-[var(--radius-md)] hover:bg-bg-hover text-text-muted transition-[background-color,color] duration-[var(--transition-fast)]"
              aria-label="Toggle sidebar"
            >
              <List size={18} weight="bold" />
            </button>
          </div>

          <div className="flex items-center gap-1">
            <NotificationBell />

            <button
              onClick={toggleTheme}
              className="p-1.5 rounded-[var(--radius-md)] hover:bg-bg-hover text-text-muted transition-[background-color,color] duration-[var(--transition-fast)]"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun size={16} weight="bold" />
              ) : (
                <Moon size={16} weight="bold" />
              )}
            </button>

            <div className="hidden sm:flex items-center gap-2 ml-1 pl-2 border-l border-border">
              <div className="h-6 w-6 rounded-full bg-accent-primary/15 flex items-center justify-center">
                <span className="text-[10px] font-bold text-accent-primary">
                  {(user?.display_name || user?.email || "U")[0].toUpperCase()}
                </span>
              </div>
              <span className="text-xs text-text-secondary">
                {user?.display_name || user?.email}
              </span>
            </div>

            <button
              onClick={logout}
              className="flex items-center gap-1.5 ml-1 px-2 py-1 rounded-[var(--radius-md)] text-xs text-text-muted hover:bg-bg-hover hover:text-text-primary transition-[background-color,color] duration-[var(--transition-fast)]"
            >
              <SignOut size={14} weight="bold" />
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
