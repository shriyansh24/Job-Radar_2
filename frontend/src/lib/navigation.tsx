import type { QueryClient } from "@tanstack/react-query";
import {
  Archive,
  Briefcase,
  Buildings,
  ChartBar,
  ChatsCircle,
  Crosshair,
  CurrencyDollar,
  EnvelopeSimple,
  FileText,
  GearSix,
  GitMerge,
  Heartbeat,
  Kanban,
  Lightning,
  MagnifyingGlassPlus,
  ShieldCheck,
  Sparkle,
  SquaresFour,
  TrendUp,
  UserCircle,
  UsersThree,
} from "@phosphor-icons/react";
import type { Icon as PhosphorIcon } from "@phosphor-icons/react";

import { analyticsApi } from "../api/analytics";
import { autoApplyApi } from "../api/auto-apply";
import { copilotApi } from "../api/copilot";
import { emailApi } from "../api/email";
import { jobsApi } from "../api/jobs";
import { networkingApi } from "../api/networking";
import { outcomesApi } from "../api/outcomes";
import { pipelineApi } from "../api/pipeline";

type WorkspaceGroup =
  | "Home"
  | "Discover"
  | "Execute"
  | "Prepare"
  | "Intelligence"
  | "Operations";

type WorkspaceRouteDefinition = {
  path: string;
  label: string;
  group: WorkspaceGroup;
  icon: PhosphorIcon;
  description: string;
  prefetch?: (queryClient: QueryClient) => void;
};

const workspaceRoutes: WorkspaceRouteDefinition[] = [
  {
    path: "/",
    label: "Command Center",
    group: "Home",
    icon: SquaresFour,
    description: "Bento overview of the current search, pipeline pressure, and next actions.",
    prefetch: (queryClient) => {
      queryClient.prefetchQuery({
        queryKey: ["analytics", "overview"],
        queryFn: () => analyticsApi.overview().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
      queryClient.prefetchQuery({
        queryKey: ["jobs", "recent"],
        queryFn: () =>
          jobsApi
            .list({ page_size: 5, sort_by: "scraped_at", sort_order: "desc" })
            .then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  },
  {
    path: "/jobs",
    label: "Jobs",
    group: "Discover",
    icon: Briefcase,
    description: "Search and triage roles with exact filters or semantic matching.",
    prefetch: (queryClient) => {
      queryClient.prefetchQuery({
        queryKey: ["jobs", { page: 1, page_size: 20, sort_by: "scraped_at", sort_order: "desc" }],
        queryFn: () =>
          jobsApi
            .list({ page: 1, page_size: 20, sort_by: "scraped_at", sort_order: "desc" })
            .then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  },
  {
    path: "/companies",
    label: "Companies",
    group: "Discover",
    icon: Buildings,
    description: "Track target companies and monitor company-level signals.",
  },
  {
    path: "/pipeline",
    label: "Pipeline",
    group: "Execute",
    icon: Kanban,
    description: "Move applications through the board and capture outcomes.",
    prefetch: (queryClient) => {
      queryClient.prefetchQuery({
        queryKey: ["pipeline"],
        queryFn: () => pipelineApi.pipeline().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  },
  {
    path: "/auto-apply",
    label: "Auto Apply",
    group: "Execute",
    icon: Lightning,
    description: "Operate profiles, rules, and background application runs.",
    prefetch: (queryClient) => {
      queryClient.prefetchQuery({
        queryKey: ["auto-apply-profiles"],
        queryFn: () => autoApplyApi.listProfiles().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
      queryClient.prefetchQuery({
        queryKey: ["auto-apply-rules"],
        queryFn: () => autoApplyApi.listRules().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
      queryClient.prefetchQuery({
        queryKey: ["auto-apply-runs"],
        queryFn: () => autoApplyApi.runs().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  },
  {
    path: "/networking",
    label: "Networking",
    group: "Execute",
    icon: UsersThree,
    description: "Manage warm contacts and referral requests.",
    prefetch: (queryClient) => {
      queryClient.prefetchQuery({
        queryKey: ["networking", "contacts"],
        queryFn: () => networkingApi.listContacts().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
      queryClient.prefetchQuery({
        queryKey: ["networking", "referral-requests"],
        queryFn: () => networkingApi.listReferralRequests().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  },
  {
    path: "/email",
    label: "Email",
    group: "Execute",
    icon: EnvelopeSimple,
    description: "Surface inbound hiring signals and parsed workflow events.",
    prefetch: (queryClient) => {
      queryClient.prefetchQuery({
        queryKey: ["email", "logs"],
        queryFn: () => emailApi.listLogs(100).then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  },
  {
    path: "/resume",
    label: "Resume Studio",
    group: "Prepare",
    icon: FileText,
    description: "Tailor resume versions and keep the source material organized.",
  },
  {
    path: "/interview",
    label: "Interview Lab",
    group: "Prepare",
    icon: ChatsCircle,
    description: "Practice answers, prompts, and interview readiness.",
  },
  {
    path: "/salary",
    label: "Compensation",
    group: "Prepare",
    icon: CurrencyDollar,
    description: "Research offers and negotiation ranges.",
  },
  {
    path: "/vault",
    label: "Vault",
    group: "Prepare",
    icon: Archive,
    description: "Store resume and cover letter assets.",
  },
  {
    path: "/copilot",
    label: "Copilot",
    group: "Prepare",
    icon: Sparkle,
    description: "Draft strategy, recall history, and generate role-specific copy.",
    prefetch: (queryClient) => {
      queryClient.prefetchQuery({
        queryKey: ["jobs", "copilot-context"],
        queryFn: () =>
          jobsApi
            .list({ page_size: 10, sort_by: "scraped_at", sort_order: "desc" })
            .then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
      queryClient.prefetchQuery({
        queryKey: ["copilot", "history"],
        queryFn: () => copilotApi.askHistory("Summarize recent application history").then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  },
  {
    path: "/analytics",
    label: "Analytics",
    group: "Intelligence",
    icon: ChartBar,
    description: "Review the overall search and pipeline metrics.",
    prefetch: (queryClient) => {
      queryClient.prefetchQuery({
        queryKey: ["analytics", "overview"],
        queryFn: () => analyticsApi.overview().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
      queryClient.prefetchQuery({
        queryKey: ["analytics", "daily"],
        queryFn: () => analyticsApi.daily(30).then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  },
  {
    path: "/outcomes",
    label: "Outcomes",
    group: "Intelligence",
    icon: TrendUp,
    description: "Analyze application outcomes and company-level response patterns.",
    prefetch: (queryClient) => {
      queryClient.prefetchQuery({
        queryKey: ["outcomes", "stats"],
        queryFn: () => outcomesApi.getStats().then((r) => r.data),
        staleTime: 5 * 60 * 1000,
      });
    },
  },
  {
    path: "/profile",
    label: "Profile",
    group: "Operations",
    icon: UserCircle,
    description: "Account profile and search preferences.",
  },
  {
    path: "/settings",
    label: "Settings",
    group: "Operations",
    icon: GearSix,
    description: "Theme, alerts, integrations, and account controls.",
  },
  {
    path: "/sources",
    label: "Sources",
    group: "Operations",
    icon: Heartbeat,
    description: "Manage scraper and ingestion sources.",
  },
  {
    path: "/targets",
    label: "Targets",
    group: "Operations",
    icon: Crosshair,
    description: "Maintain target companies and outreach focus.",
  },
  {
    path: "/canonical-jobs",
    label: "Canonical Jobs",
    group: "Operations",
    icon: GitMerge,
    description: "Normalize duplicate jobs into canonical records.",
  },
  {
    path: "/search-expansion",
    label: "Search Expansion",
    group: "Operations",
    icon: MagnifyingGlassPlus,
    description: "Broaden and tune the search surface.",
  },
  {
    path: "/admin",
    label: "Admin",
    group: "Operations",
    icon: ShieldCheck,
    description: "Health checks, exports, imports, and maintenance.",
  },
];

const workspaceSectionOrder: WorkspaceGroup[] = [
  "Home",
  "Discover",
  "Execute",
  "Prepare",
  "Intelligence",
  "Operations",
];

const workspaceSections = workspaceSectionOrder.map((group) => ({
  label: group,
  items: workspaceRoutes.filter((route) => route.group === group),
}));

const mobilePrimaryRoutes = ["/", "/jobs", "/pipeline", "/analytics", "/networking"]
  .map((path) => workspaceRoutes.find((route) => route.path === path))
  .filter((route): route is WorkspaceRouteDefinition => Boolean(route));

function getWorkspaceRoute(pathname: string): WorkspaceRouteDefinition | null {
  const normalized = pathname === "/" ? "/" : pathname.replace(/\/+$/, "");
  return workspaceRoutes.find((route) => route.path === normalized) ?? null;
}

function prefetchWorkspaceRoute(pathname: string, queryClient: QueryClient): void {
  getWorkspaceRoute(pathname)?.prefetch?.(queryClient);
}

export type { WorkspaceGroup, WorkspaceRouteDefinition };
export {
  getWorkspaceRoute,
  prefetchWorkspaceRoute,
  mobilePrimaryRoutes,
  workspaceRoutes,
  workspaceSections,
  workspaceSectionOrder,
};
