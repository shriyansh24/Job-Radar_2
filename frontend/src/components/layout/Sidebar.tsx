import { TerminalWindow } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import { NavLink } from "react-router-dom";

import {
  prefetchWorkspaceRoute,
  workspaceSections,
} from "../../lib/navigation";
import { cn } from "../../lib/utils";
import { useUIStore } from "../../store/useUIStore";

const sectionTitles: Record<string, string> = {
  Home: "Core Command",
  Discover: "Discovery",
  Execute: "Execution",
  Prepare: "AI Tools",
  Intelligence: "Intelligence",
  Operations: "System Data",
};

export default function Sidebar() {
  const collapsed = useUIStore((state) => state.sidebarCollapsed);
  const queryClient = useQueryClient();

  return (
    <aside
      className={cn(
        "fixed left-0 top-[var(--header-height)] z-40 hidden h-[calc(100dvh-var(--header-height))] border-r-2 border-border bg-[var(--sidebar-bg)] xl:flex xl:flex-col",
        collapsed ? "w-[var(--sidebar-width-collapsed)]" : "w-[var(--sidebar-width)]"
      )}
    >
      <div className="border-b-2 border-border px-4 py-5">
        <div className="flex items-start gap-3">
          <div className="flex size-11 shrink-0 items-center justify-center border-2 border-border bg-foreground text-background">
            <TerminalWindow size={18} weight="bold" />
          </div>
          {!collapsed ? (
            <div className="min-w-0">
              <h2 className="font-display text-xl font-black uppercase tracking-[-0.06em] text-foreground">
                JobRadar
              </h2>
            </div>
          ) : (
            <span className="sr-only">JobRadar command center navigation</span>
          )}
        </div>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        {workspaceSections.map((section) => (
          <div key={section.label} className="space-y-2">
            {!collapsed ? (
              <div className="label px-2">{sectionTitles[section.label] ?? section.label}</div>
            ) : null}
            <div className="space-y-1">
              {section.items.map(({ path, icon: Icon, label }) => (
                <NavLink
                  key={path}
                  to={path}
                  onMouseEnter={() => prefetchWorkspaceRoute(path, queryClient)}
                  className={({ isActive }) =>
                    cn(
                      "group hard-press flex items-center gap-3 border-2 px-3 py-3 transition-[transform,box-shadow,background-color,color,border-color]",
                      collapsed ? "justify-center" : "justify-start",
                      isActive
                        ? "border-border bg-[var(--sidebar-item-active-bg)] text-[var(--sidebar-item-active-text)]"
                        : "border-transparent bg-transparent text-text-secondary hover:border-border hover:bg-[var(--sidebar-item-hover)] hover:text-foreground"
                    )
                  }
                >
                  <motion.span
                    aria-hidden="true"
                    className="inline-flex shrink-0"
                    whileHover={{ x: collapsed ? 0 : 2 }}
                    transition={{ type: "spring", stiffness: 320, damping: 22 }}
                  >
                    <Icon size={18} weight="bold" />
                  </motion.span>
                  {!collapsed ? (
                    <span className="truncate font-mono text-[11px] font-bold uppercase tracking-[0.18em]">
                      {label}
                    </span>
                  ) : null}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
