import React, { useState } from "react";
import { Outlet, Link, useLocation, useNavigate } from "react-router";
import { 
  Menu, Search, Moon, Sun, Bell, X, List,
  LayoutDashboard, Briefcase, Building2, Kanban, Zap, Users,
  Mail, FileText, MessageCircle, DollarSign, Archive, Sparkles,
  BarChart2, TrendingUp, UserCircle, Settings, Activity,
  Target, GitMerge, ZoomIn, ShieldCheck, LogOut
} from "lucide-react";
import { cn } from "@/lib/utils";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { useTheme } from "./theme-provider";

function cn2(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const workspaceRoutes = [
  { path: "/", label: "Command Center", group: "Home", icon: LayoutDashboard, description: "Bento overview of the current search, pipeline pressure, and next actions." },
  { path: "/jobs", label: "Jobs", group: "Discover", icon: Briefcase, description: "Search and triage roles with exact filters or semantic matching." },
  { path: "/companies", label: "Companies", group: "Discover", icon: Building2, description: "Track target companies and monitor company-level signals." },
  { path: "/pipeline", label: "Pipeline", group: "Execute", icon: Kanban, description: "Move applications through the board and capture outcomes." },
  { path: "/auto-apply", label: "Auto Apply", group: "Execute", icon: Zap, description: "Operate profiles, rules, and background application runs." },
  { path: "/networking", label: "Networking", group: "Execute", icon: Users, description: "Manage warm contacts and referral requests." },
  { path: "/email", label: "Email", group: "Execute", icon: Mail, description: "Surface inbound hiring signals and parsed workflow events." },
  { path: "/resume", label: "Resume Studio", group: "Prepare", icon: FileText, description: "Tailor resume versions and keep the source material organized." },
  { path: "/interview", label: "Interview Lab", group: "Prepare", icon: MessageCircle, description: "Practice answers, prompts, and interview readiness." },
  { path: "/salary", label: "Compensation", group: "Prepare", icon: DollarSign, description: "Research offers and negotiation ranges." },
  { path: "/vault", label: "Vault", group: "Prepare", icon: Archive, description: "Store resume and cover letter assets." },
  { path: "/copilot", label: "Copilot", group: "Prepare", icon: Sparkles, description: "Draft strategy, recall history, and generate role-specific copy." },
  { path: "/analytics", label: "Analytics", group: "Intelligence", icon: BarChart2, description: "Review the overall search and pipeline metrics." },
  { path: "/outcomes", label: "Outcomes", group: "Intelligence", icon: TrendingUp, description: "Analyze application outcomes and company-level response patterns." },
  { path: "/profile", label: "Profile", group: "Operations", icon: UserCircle, description: "Account profile and search preferences." },
  { path: "/settings", label: "Settings", group: "Operations", icon: Settings, description: "Theme, alerts, integrations, and account controls." },
  { path: "/sources", label: "Sources", group: "Operations", icon: Activity, description: "Manage scraper and ingestion sources." },
  { path: "/targets", label: "Targets", group: "Operations", icon: Target, description: "Maintain target companies and outreach focus." },
  { path: "/canonical-jobs", label: "Canonical Jobs", group: "Operations", icon: GitMerge, description: "Normalize duplicate jobs into canonical records." },
  { path: "/search-expansion", label: "Search Expansion", group: "Operations", icon: ZoomIn, description: "Broaden and tune the search surface." },
  { path: "/admin", label: "Admin", group: "Operations", icon: ShieldCheck, description: "Health checks, exports, imports, and maintenance." },
];

const workspaceSectionOrder = [
  "Home", "Discover", "Execute", "Prepare", "Intelligence", "Operations"
];

export function AppShell() {
  const { mode, toggleMode } = useTheme();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const currentRoute = workspaceRoutes.find(r => r.path === location.pathname) || workspaceRoutes[0];

  const headerButtonClass =
    "hard-press inline-flex size-10 items-center justify-center border-2 border-border bg-background text-foreground hover:bg-card shadow-hard-sm";

  return (
    <div className="flex h-screen w-full flex-col bg-background text-foreground overflow-hidden">
      {/* Header */}
      <header className="flex h-[var(--header-height,4rem)] shrink-0 items-center justify-between gap-3 border-b-2 border-border bg-background px-3 sm:px-5 relative z-20 shadow-hard-xl">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileNavOpen(!mobileNavOpen)}
            className={cn2(headerButtonClass, "lg:hidden")}
          >
            {mobileNavOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          
          <button
            type="button"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className={cn2(headerButtonClass, "hidden lg:inline-flex")}
          >
            <List size={18} />
          </button>

          <div className="flex items-center gap-3">
            <div className="hidden size-10 items-center justify-center border-2 border-border bg-primary text-sm font-black uppercase text-primary-foreground sm:flex">
              JR
            </div>
            <div>
              <p className="font-headline text-2xl font-black uppercase tracking-tighter">JobRadar V2</p>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-black uppercase tracking-tighter sm:text-lg truncate font-headline text-muted-foreground">
                  {currentRoute.label}
                </h1>
                <span className="hidden font-mono text-[10px] uppercase tracking-widest text-muted-foreground lg:inline">
                  {currentRoute.group}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="hidden flex-1 justify-center lg:flex">
          <button className="hard-press flex w-full max-w-[400px] items-center gap-3 border-2 border-border bg-card px-4 py-2 text-left text-sm text-muted-foreground shadow-hard-sm">
            <Search size={16} />
            <span className="font-mono text-[11px] uppercase tracking-widest">
              Command search...
            </span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-2 border-2 border-border bg-card px-3 py-2 lg:flex shadow-hard-sm">
            <span className="command-label">System status</span>
            <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-green-500">
              Optimal
            </span>
          </div>

          <button className={headerButtonClass}>
            <Bell size={16} />
          </button>

          <button onClick={toggleMode} className={headerButtonClass}>
            {mode === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          <div className="hidden items-center gap-3 border-2 border-border bg-card px-3 py-1.5 sm:flex shadow-hard-sm">
            <div className="flex size-7 items-center justify-center border-2 border-border bg-muted font-mono text-xs font-bold uppercase">
              O
            </div>
            <div className="min-w-0">
              <p className="command-label">Active operator</p>
              <p className="text-sm font-medium">Operator</p>
            </div>
          </div>
          
          <button onClick={() => navigate('/login')} className="hard-press hidden items-center gap-2 border-2 border-border bg-foreground px-3 py-2 text-[11px] font-bold uppercase tracking-widest text-background sm:inline-flex shadow-hard-sm">
            <LogOut size={14} />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Desktop Sidebar */}
        <aside
          className={cn2(
            "hidden border-r-2 border-border bg-secondary transition-all duration-300 lg:flex flex-col overflow-y-auto",
            sidebarCollapsed ? "w-20" : "w-64"
          )}
        >
          <div className="flex-1 space-y-6 py-4">
            {workspaceSectionOrder.map((group) => {
              const items = workspaceRoutes.filter(r => r.group === group);
              if (items.length === 0) return null;
              
              return (
                <div key={group} className="space-y-1">
                  {!sidebarCollapsed && (
                    <div className="px-4 mb-2 command-label text-[9px]">{group}</div>
                  )}
                  {items.map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        className={cn2(
                          "flex items-center gap-3 border-y-2 border-transparent px-4 py-2.5 mx-2 hard-press",
                          isActive 
                            ? "border-border bg-primary text-primary-foreground shadow-hard-sm" 
                            : "text-foreground hover:border-border hover:bg-card border-2"
                        )}
                        title={sidebarCollapsed ? item.label : undefined}
                      >
                        <item.icon size={18} className={cn2("shrink-0", isActive ? "text-primary-foreground" : "")} />
                        {!sidebarCollapsed && (
                          <span className="font-mono text-[11px] font-bold uppercase tracking-widest truncate">
                            {item.label}
                          </span>
                        )}
                      </Link>
                    )
                  })}
                </div>
              );
            })}
          </div>
        </aside>

        {/* Mobile Navigation Drawer */}
        {mobileNavOpen && (
          <div className="absolute inset-0 z-30 lg:hidden flex">
            <div 
              className="absolute inset-0 bg-background/80 backdrop-blur-sm" 
              onClick={() => setMobileNavOpen(false)}
            />
            <div className="relative w-64 h-full border-r-2 border-border bg-secondary overflow-y-auto shadow-xl">
              <div className="p-4 border-b-2 border-border">
                <p className="command-label">Navigation</p>
                <h2 className="mt-2 font-headline text-xl font-black uppercase tracking-tighter">
                  Command Center
                </h2>
              </div>
              <div className="py-4 space-y-6">
                {workspaceSectionOrder.map((group) => {
                  const items = workspaceRoutes.filter(r => r.group === group);
                  if (items.length === 0) return null;
                  return (
                    <div key={group} className="space-y-1">
                      <div className="px-4 mb-2 command-label text-[9px]">{group}</div>
                      {items.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            onClick={() => setMobileNavOpen(false)}
                            className={cn2(
                              "flex items-center gap-3 border-2 mx-2 px-3 py-2 hard-press",
                              isActive 
                                ? "border-border bg-primary text-primary-foreground shadow-hard-sm" 
                                : "border-transparent text-foreground hover:border-border hover:bg-card"
                            )}
                          >
                            <item.icon size={18} />
                            <span className="font-mono text-[11px] font-bold uppercase tracking-widest">
                              {item.label}
                            </span>
                          </Link>
                        )
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Content Area */}
        <main className="flex-1 overflow-auto bg-background p-4 sm:p-6">
          <div className="mx-auto h-full max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}