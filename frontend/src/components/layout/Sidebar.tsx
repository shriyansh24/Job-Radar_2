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

const navItems = [
  { to: "/", icon: SquaresFour, label: "Dashboard" },
  { to: "/jobs", icon: Briefcase, label: "Job Board" },
  { to: "/pipeline", icon: Kanban, label: "Pipeline" },
  { to: "/auto-apply", icon: Lightning, label: "Auto Apply" },
  { to: "/resume", icon: FileText, label: "Resume" },
  { to: "/interview", icon: ChatsCircle, label: "Interview" },
  { to: "/salary", icon: CurrencyDollar, label: "Salary" },
  { to: "/vault", icon: Archive, label: "Vault" },
  { to: "/analytics", icon: ChartBar, label: "Analytics" },
  { to: "/settings", icon: GearSix, label: "Settings" },
  { to: "/companies", icon: Buildings, label: "Companies" },
  { to: "/sources", icon: Heartbeat, label: "Sources" },
  { to: "/canonical-jobs", icon: GitMerge, label: "Canonical Jobs" },
  { to: "/search-expansion", icon: MagnifyingGlassPlus, label: "Search Expansion" },
  { to: "/targets", icon: Crosshair, label: "Targets" },
  { to: "/admin", icon: ShieldCheck, label: "Admin" },
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
        "min-h-[100dvh] bg-bg-secondary border-r border-border flex flex-col transition-[width] duration-[var(--transition-normal)]",
        collapsed ? "w-[4.25rem]" : "w-72"
      )}
    >
      <div className="p-4 border-b border-border">
        <h1
          className={cn(
            "font-semibold tracking-tight text-text-primary",
            collapsed ? "text-center text-sm" : "text-base"
          )}
        >
          {collapsed ? (
            <span className="font-mono text-text-secondary">JR</span>
          ) : (
            <span className="flex items-baseline gap-2">
              <span>JobRadar</span>
              <span className="font-mono text-xs text-text-muted">v2</span>
            </span>
          )}
        </h1>
      </div>
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onMouseEnter={() => prefetchMap[to]?.()}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] text-sm transition-[background-color,color,transform] duration-[var(--transition-fast)]",
                isActive
                  ? "bg-bg-tertiary text-text-primary"
                  : "text-text-secondary hover:bg-bg-tertiary hover:text-text-primary"
              )
            }
          >
            <motion.span
              aria-hidden="true"
              className="inline-flex"
              whileHover={{ x: 2 }}
              transition={{ type: "spring", stiffness: 220, damping: 18 }}
            >
              <Icon size={20} weight="bold" />
            </motion.span>
            {!collapsed && (
              <span className="truncate">{label}</span>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
