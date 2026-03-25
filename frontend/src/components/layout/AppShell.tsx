import {
  List,
  MagnifyingGlass,
  Moon,
  SignOut,
  Sun,
  X,
} from "@phosphor-icons/react";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useAuthStore } from "../../store/useAuthStore";
import { useUIStore } from "../../store/useUIStore";
import {
  getWorkspaceRoute,
  mobilePrimaryRoutes,
  workspaceSections,
} from "../../lib/navigation";
import { cn } from "../../lib/utils";
import ScraperLog from "../scraper/ScraperLog";
import { WorkspaceShell } from "../system";
import NotificationBell from "./NotificationBell";
import Sidebar from "./Sidebar";

function navLinkActive(targetPath: string, pathname: string) {
  if (targetPath === "/") return pathname === "/";
  return pathname === targetPath;
}

export default function AppShell() {
  const location = useLocation();
  const pathname = location.pathname;
  const currentRoute = getWorkspaceRoute(pathname);

  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed);
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  const mobileNavOpen = useUIStore((state) => state.mobileNavOpen);
  const setMobileNavOpen = useUIStore((state) => state.setMobileNavOpen);
  const toggleMobileNav = useUIStore((state) => state.toggleMobileNav);
  const theme = useUIStore((state) => state.theme);
  const toggleTheme = useUIStore((state) => state.toggleTheme);

  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const showScraperLog = currentRoute?.group === "Operations";

  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname, setMobileNavOpen]);

  const headerButtonClass =
    "hard-press inline-flex size-10 items-center justify-center border-2 border-border bg-background text-foreground shadow-[var(--shadow-xs)]";

  return (
    <WorkspaceShell
      sidebar={<Sidebar />}
      sidebarCollapsed={sidebarCollapsed}
      contentClassName="pb-24 lg:pb-8"
      header={
        <div className="flex h-[var(--header-height)] items-center justify-between gap-3 px-3 sm:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              onClick={toggleMobileNav}
              className={cn(headerButtonClass, "xl:hidden")}
              aria-label="Open navigation"
            >
              {mobileNavOpen ? <X size={18} weight="bold" /> : <List size={18} weight="bold" />}
            </button>

            <button
              type="button"
              onClick={toggleSidebar}
              className={cn(headerButtonClass, "hidden xl:inline-flex")}
              aria-label="Collapse navigation"
            >
              <List size={18} weight="bold" />
            </button>

            <div className="flex min-w-0 items-center gap-3">
              <div className="hidden size-10 items-center justify-center border-2 border-border bg-primary text-sm font-black uppercase text-primary-foreground shadow-[var(--shadow-xs)] sm:flex">
                JR
              </div>
              <div className="min-w-0">
                <p className="command-label">JobRadar V2</p>
                <div className="flex min-w-0 items-center gap-2">
                  <h1 className="truncate text-base font-black uppercase tracking-[-0.08em] text-foreground sm:text-lg">
                    {currentRoute?.label ?? "Command Center"}
                  </h1>
                  {currentRoute?.group ? (
                    <span className="hidden font-mono text-[10px] uppercase tracking-[0.18em] text-text-muted lg:inline">
                      {currentRoute.group}
                    </span>
                  ) : null}
                  {currentRoute?.description ? (
                    <span className="hidden truncate text-sm text-text-muted xl:inline">
                      {currentRoute.description}
                    </span>
                  ) : null}
                </div>
              </div>
            </div>
          </div>

          <div className="hidden min-w-0 flex-1 justify-center lg:flex">
            <button
              type="button"
              className="hard-press flex min-w-[320px] max-w-[540px] flex-1 items-center gap-3 border-2 border-border bg-card px-4 py-3 text-left text-sm text-text-muted shadow-[var(--shadow-xs)]"
            >
              <MagnifyingGlass size={16} weight="bold" />
              <span className="font-mono text-[11px] uppercase tracking-[0.18em]">
                Command search...
              </span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden items-center gap-2 border-2 border-border bg-card px-3 py-2 shadow-[var(--shadow-xs)] lg:flex">
              <span className="command-label">System status</span>
              <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-accent-success">
                Optimal
              </span>
            </div>

            <NotificationBell />

            <button
              type="button"
              onClick={toggleTheme}
              className={headerButtonClass}
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun size={16} weight="bold" />
              ) : (
                <Moon size={16} weight="bold" />
              )}
            </button>

            <div className="hidden items-center gap-3 border-2 border-border bg-card px-3 py-2 shadow-[var(--shadow-xs)] sm:flex">
              <div className="flex size-8 items-center justify-center border-2 border-border bg-[var(--color-bg-tertiary)] font-mono text-xs font-bold uppercase text-foreground">
                {(user?.display_name || user?.email || "U")[0].toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="command-label">Active operator</p>
                <p className="max-w-40 truncate text-sm font-medium text-foreground">
                  {user?.display_name || user?.email}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={logout}
              className="hard-press inline-flex items-center gap-2 border-2 border-border bg-foreground px-3 py-2 text-[11px] font-bold uppercase tracking-[0.18em] text-background shadow-[var(--shadow-sm)]"
            >
              <SignOut size={14} weight="bold" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      }
      bottomNav={
        <nav className="fixed inset-x-0 bottom-0 z-40 border-t-2 border-border bg-background lg:hidden">
          <div className="grid h-20 grid-cols-5">
            {mobilePrimaryRoutes.map((route) => {
              const active = navLinkActive(route.path, pathname);
              const Icon = route.icon;
              return (
                <NavLink
                  key={route.path}
                  to={route.path}
                  className={cn(
                    "flex flex-col items-center justify-center gap-1 border-r-2 border-border px-2 text-foreground transition-colors last:border-r-0",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "bg-background hover:bg-card"
                  )}
                >
                  <Icon size={18} weight={active ? "fill" : "bold"} />
                  <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em]">
                    {route.group === "Home" ? "Radar" : route.label}
                  </span>
                </NavLink>
              );
            })}
          </div>
        </nav>
      }
    >
      <AnimatePresence>
        {mobileNavOpen ? (
          <>
            <motion.button
              type="button"
              className="fixed inset-0 z-30 bg-black/65 xl:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileNavOpen(false)}
              aria-label="Close navigation"
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 260, damping: 28 }}
              className="fixed left-0 top-[var(--header-height)] z-40 h-[calc(100dvh-var(--header-height))] w-[min(22rem,100vw)] overflow-y-auto border-r-2 border-border bg-background px-4 py-5 xl:hidden"
            >
              <div className="space-y-6">
                <div className="border-2 border-border bg-card p-4 shadow-[var(--shadow-sm)]">
                  <p className="command-label">Navigation</p>
                  <h2 className="mt-2 text-xl font-black uppercase tracking-[-0.08em]">
                    Command Center
                  </h2>
                  <p className="mt-2 text-sm text-text-secondary">
                    Move across discovery, execution, intelligence, and operations.
                  </p>
                </div>

                {workspaceSections.map((section) => (
                  <div key={section.label} className="space-y-2">
                    <div className="label">{section.label}</div>
                    <div className="space-y-1">
                      {section.items.map(({ path, icon: Icon, label }) => (
                        <NavLink
                          key={path}
                          to={path}
                          className={({ isActive }) =>
                            cn(
                              "hard-press flex items-center gap-3 border-2 px-3 py-3",
                              isActive
                                ? "border-border bg-primary text-primary-foreground shadow-[var(--shadow-sm)]"
                                : "border-transparent bg-transparent text-foreground hover:border-border hover:bg-card"
                            )
                          }
                        >
                          <Icon size={18} weight="bold" />
                          <span className="font-mono text-[11px] font-bold uppercase tracking-[0.18em]">
                            {label}
                          </span>
                        </NavLink>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </motion.aside>
          </>
        ) : null}
      </AnimatePresence>

      <div className="min-h-0">
        <Outlet />
      </div>
      {showScraperLog ? <ScraperLog /> : null}
    </WorkspaceShell>
  );
}
