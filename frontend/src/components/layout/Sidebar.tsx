import { motion } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import { NavLink, useLocation } from "react-router-dom";
import { getWorkspaceRoute, prefetchWorkspaceRoute, workspaceSections } from "../../lib/navigation";
import { cn } from "../../lib/utils";
import { useUIStore } from "../../store/useUIStore";

export default function Sidebar() {
  const collapsed = useUIStore((s) => s.sidebarCollapsed);
  const queryClient = useQueryClient();
  const location = useLocation();
  const currentRoute = getWorkspaceRoute(location.pathname);

  return (
    <aside
      className={cn(
        "min-h-[100dvh] border-r border-border flex flex-col transition-[width] duration-[var(--transition-normal)]",
        collapsed ? "w-[4.25rem]" : "w-60",
        "bg-[var(--sidebar-bg)]"
      )}
    >
      <div className="border-b border-border px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] border border-border bg-bg-secondary text-sm font-semibold text-accent-primary shadow-[var(--shadow-xs)]">
            JR
          </div>
          {!collapsed ? (
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold tracking-[-0.02em] text-text-primary">
                  JobRadar
                </h1>
                <span className="rounded-full border border-border bg-bg-secondary px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.18em] text-text-muted">
                  Career OS
                </span>
              </div>
              <p className="mt-1 truncate text-xs text-text-muted">
                {currentRoute?.label ?? "Command Center"}
              </p>
            </div>
          ) : (
            <span className="sr-only">JobRadar Career OS</span>
          )}
        </div>
      </div>
      <nav className="flex-1 px-2 py-3 overflow-y-auto space-y-5">
        {workspaceSections.map((section, i) => (
          <div key={i}>
            {section.label && !collapsed && (
              <div className="label px-3 mb-1.5">{section.label}</div>
            )}
            {collapsed && i > 0 && (
              <div className="mx-3 mb-2 h-px bg-border" />
            )}
            <div className="space-y-0.5">
              {section.items.map(({ path, icon: Icon, label }) => (
                <NavLink
                  key={path}
                  to={path}
                  onMouseEnter={() => prefetchWorkspaceRoute(path, queryClient)}
                  className={({ isActive }) =>
                    cn(
                      "group relative flex items-center gap-3 px-3 py-2 rounded-[var(--radius-md)] text-[13px] transition-[background-color,color] duration-[var(--transition-fast)]",
                      isActive
                        ? "bg-accent-primary/8 text-accent-primary font-medium sidebar-active-indicator"
                        : "text-text-secondary hover:bg-bg-hover hover:text-text-primary"
                    )
                  }
                >
                  <motion.span
                    aria-hidden="true"
                    className="inline-flex shrink-0"
                    whileHover={{ x: 2 }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  >
                    <Icon size={18} weight="bold" />
                  </motion.span>
                  {!collapsed && (
                    <span className="truncate">{label}</span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
