import {
  Archive,
  Briefcase,
  Buildings,
  ChartBar,
  ChatsCircle,
  Crosshair,
  CurrencyDollar,
  FileText,
  GearSix,
  GitMerge,
  Heartbeat,
  Kanban,
  Lightning,
  MagnifyingGlassPlus,
  ShieldCheck,
  SquaresFour,
} from "@phosphor-icons/react";
import { useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { NavLink } from "react-router-dom";
import { analyticsApi } from "../../api/analytics";
import { jobsApi } from "../../api/jobs";
import { pipelineApi } from "../../api/pipeline";
import { cn } from "../../lib/utils";
import { useUIStore } from "../../store/useUIStore";

const mainNav = [
  { to: "/", icon: SquaresFour, label: "Dashboard" },
  { to: "/jobs", icon: Briefcase, label: "Job Board" },
  { to: "/pipeline", icon: Kanban, label: "Pipeline" },
  { to: "/auto-apply", icon: Lightning, label: "Auto Apply" },
];

const toolsNav = [
  { to: "/resume", icon: FileText, label: "Resume" },
  { to: "/interview", icon: ChatsCircle, label: "Interview" },
  { to: "/salary", icon: CurrencyDollar, label: "Salary" },
  { to: "/vault", icon: Archive, label: "Vault" },
  { to: "/analytics", icon: ChartBar, label: "Analytics" },
];

const adminNav = [
  { to: "/settings", icon: GearSix, label: "Settings" },
  { to: "/companies", icon: Buildings, label: "Companies" },
  { to: "/sources", icon: Heartbeat, label: "Sources" },
  { to: "/canonical-jobs", icon: GitMerge, label: "Canonical Jobs" },
  { to: "/search-expansion", icon: MagnifyingGlassPlus, label: "Search Expansion" },
  { to: "/targets", icon: Crosshair, label: "Targets" },
  { to: "/admin", icon: ShieldCheck, label: "Admin" },
];

const navSections = [
  { items: mainNav },
  { label: "Tools", items: toolsNav },
  { label: "Manage", items: adminNav },
];

export default function Sidebar() {
  const collapsed = useUIStore((s) => s.sidebarCollapsed);
  const queryClient = useQueryClient();

  const prefetchMap: Record<string, () => void> = {
    '/': () => queryClient.prefetchQuery({
      queryKey: ['analytics', 'overview'],
      queryFn: () => analyticsApi.overview().then((r) => r.data),
      staleTime: 5 * 60 * 1000,
    }),
    '/jobs': () => queryClient.prefetchQuery({
      queryKey: ['jobs', { page: 1, page_size: 20, sort_by: 'scraped_at', sort_order: 'desc' }],
      queryFn: () => jobsApi.list({ page: 1, page_size: 20, sort_by: 'scraped_at', sort_order: 'desc' }).then((r) => r.data),
      staleTime: 5 * 60 * 1000,
    }),
    '/pipeline': () => queryClient.prefetchQuery({
      queryKey: ['pipeline'],
      queryFn: () => pipelineApi.pipeline().then((r) => r.data),
      staleTime: 5 * 60 * 1000,
    }),
    '/analytics': () => {
      queryClient.prefetchQuery({
        queryKey: ['analytics', 'overview'],
        queryFn: () => analyticsApi.overview().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
      queryClient.prefetchQuery({
        queryKey: ['analytics', 'daily'],
        queryFn: () => analyticsApi.daily(30).then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  };

  return (
    <aside
      className={cn(
        "min-h-[100dvh] border-r border-border flex flex-col transition-[width] duration-[var(--transition-normal)]",
        collapsed ? "w-[4.25rem]" : "w-60",
        "bg-[var(--sidebar-bg)]"
      )}
    >
      <div className="h-14 flex items-center px-4 border-b border-border">
        <h1
          className={cn(
            "font-semibold tracking-tight text-text-primary",
            collapsed ? "text-center text-sm w-full" : "text-sm"
          )}
        >
          {collapsed ? (
            <span className="font-mono text-accent-primary font-bold">JR</span>
          ) : (
            <span className="flex items-baseline gap-1.5">
              <span className="tracking-[-0.02em]">JobRadar</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-[var(--radius-sm)] bg-accent-primary/10 text-accent-primary font-medium">
                v2
              </span>
            </span>
          )}
        </h1>
      </div>
      <nav className="flex-1 px-2 py-3 overflow-y-auto space-y-5">
        {navSections.map((section, i) => (
          <div key={i}>
            {section.label && !collapsed && (
              <div className="label px-3 mb-1.5">{section.label}</div>
            )}
            {collapsed && i > 0 && (
              <div className="mx-3 mb-2 h-px bg-border" />
            )}
            <div className="space-y-0.5">
              {section.items.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  onMouseEnter={() => prefetchMap[to]?.()}
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
