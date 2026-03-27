import {
  ArrowClockwise,
  ChartBar,
  CheckCircle,
  Clock,
  Envelope,
  Lightning,
  Plus,
  Pulse,
  Shield,
  ShieldCheck,
  Pause,
  Play,
  User,
  XCircle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { autoApplyApi, type AutoApplyRule } from "../api/auto-apply";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import { SkeletonCard } from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import { toast } from "../components/ui/toastService";
import { cn } from "../lib/utils";
import { CreateProfileModal } from "../components/auto-apply/CreateProfileModal";
import { CreateRuleModal } from "../components/auto-apply/CreateRuleModal";
import { ProfileCard } from "../components/auto-apply/ProfileCard";
import { RuleCard } from "../components/auto-apply/RuleCard";
import { RunRow } from "../components/auto-apply/RunRow";
import { CHIP } from "../components/auto-apply/autoApplyUtils";

const TABS = [
  { id: "profiles", label: "Profiles", icon: <User size={14} weight="bold" /> },
  { id: "rules", label: "Rules", icon: <Shield size={14} weight="bold" /> },
  { id: "history", label: "Run History", icon: <Clock size={14} weight="bold" /> },
  { id: "stats", label: "Statistics", icon: <ChartBar size={14} weight="bold" /> },
] as const;

export default function AutoApply() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("profiles");
  const [showCreateProfile, setShowCreateProfile] = useState(false);
  const [showCreateRule, setShowCreateRule] = useState(false);

  const { data: profiles, isLoading: profilesLoading } = useQuery({
    queryKey: ["auto-apply-profiles"],
    queryFn: () => autoApplyApi.listProfiles().then((response) => response.data),
  });

  const { data: rules, isLoading: rulesLoading } = useQuery({
    queryKey: ["auto-apply-rules"],
    queryFn: () => autoApplyApi.listRules().then((response) => response.data),
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["auto-apply-stats"],
    queryFn: () => autoApplyApi.getStats().then((response) => response.data),
  });

  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ["auto-apply-runs"],
    queryFn: () => autoApplyApi.runs().then((response) => response.data),
  });

  const runNowMutation = useMutation({
    mutationFn: () => autoApplyApi.run(),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["auto-apply-runs"] }),
        queryClient.invalidateQueries({ queryKey: ["auto-apply-stats"] }),
      ]);
      toast("success", "Auto-apply run triggered");
      setActiveTab("history");
    },
    onError: () => toast("error", "Failed to trigger auto-apply"),
  });

  const pauseMutation = useMutation({
    mutationFn: () => autoApplyApi.pause(),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["auto-apply-rules"] }),
        queryClient.invalidateQueries({ queryKey: ["auto-apply-runs"] }),
        queryClient.invalidateQueries({ queryKey: ["auto-apply-stats"] }),
      ]);
      toast("success", "Auto-apply pause sent");
    },
    onError: () => toast("error", "Failed to pause auto-apply"),
  });

  const toggleRuleMutation = useMutation({
    mutationFn: (rule: AutoApplyRule) =>
      autoApplyApi.updateRule(rule.id, {
        name: rule.name ?? undefined,
        is_active: !rule.is_active,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auto-apply-rules"] });
      toast("success", "Rule updated");
    },
    onError: () => toast("error", "Failed to update rule"),
  });

  const activeRuleCount = rules?.filter((rule) => rule.is_active).length ?? 0;
  const successRate =
    stats && stats.total_runs > 0 ? Math.round((stats.successful / stats.total_runs) * 100) : 0;
  const latestRun = useMemo(
    () =>
      [...(runs ?? [])].sort((left, right) => {
        const leftStamp = left.started_at ?? left.completed_at ?? "";
        const rightStamp = right.started_at ?? right.completed_at ?? "";
        return rightStamp.localeCompare(leftStamp);
      })[0] ?? null,
    [runs]
  );
  const operatorBusy = runNowMutation.isPending || pauseMutation.isPending;

  const metricItems = useMemo(
    () => [
      {
        key: "profiles",
        label: "Profiles",
        value: profilesLoading ? "..." : String(profiles?.length ?? 0),
        hint: "Profiles ready for automation.",
        tone: "default" as const,
      },
      {
        key: "rules",
        label: "Active Rules",
        value: rulesLoading ? "..." : String(activeRuleCount),
        hint: "Rules allowed to fire.",
        tone: "warning" as const,
      },
      {
        key: "runs",
        label: "Runs",
        value: statsLoading ? "..." : String(stats?.total_runs ?? 0),
        hint: "Execution attempts recorded.",
        tone: latestRun?.status === "failed" ? ("danger" as const) : ("success" as const),
      },
      {
        key: "success",
        label: "Success Rate",
        value: statsLoading ? "..." : `${successRate}%`,
        hint: "Completed runs / total runs.",
        tone: "danger" as const,
      },
    ],
    [activeRuleCount, latestRun?.status, profiles?.length, profilesLoading, rulesLoading, stats, statsLoading, successRate]
  );

  const headerActions = (
    <>
      <Button
        variant="secondary"
        onClick={() => {
          queryClient.invalidateQueries({ queryKey: ["auto-apply-rules"] });
          queryClient.invalidateQueries({ queryKey: ["auto-apply-runs"] });
          queryClient.invalidateQueries({ queryKey: ["auto-apply-stats"] });
        }}
        icon={<ArrowClockwise size={16} weight="bold" />}
      >
        Refresh
      </Button>
      <Button
        variant="secondary"
        loading={pauseMutation.isPending}
        disabled={operatorBusy}
        onClick={() => pauseMutation.mutate()}
        icon={<Pause size={16} weight="bold" />}
      >
        Pause
      </Button>
      <Button
        loading={runNowMutation.isPending}
        disabled={operatorBusy}
        onClick={() => runNowMutation.mutate()}
        icon={<Play size={16} weight="bold" />}
      >
        Run now
      </Button>
      {activeTab === "profiles" ? (
        <Button variant="secondary" onClick={() => setShowCreateProfile(true)} icon={<Plus size={16} weight="bold" />}>
          Add Profile
        </Button>
      ) : activeTab === "rules" ? (
        <Button variant="secondary" onClick={() => setShowCreateRule(true)} icon={<Plus size={16} weight="bold" />}>
          Add Rule
        </Button>
      ) : null}
    </>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Execute"
        title="Auto Apply"
        description="Profiles, rules, and run history."
        meta={
          <>
            <span className={cn(CHIP, "bg-bg-secondary text-text-primary")}>{profiles?.length ?? 0} profiles</span>
            <span className={cn(CHIP, "bg-bg-secondary text-text-primary")}>{activeRuleCount} active rules</span>
            <span className={cn(CHIP, "bg-bg-secondary text-text-primary")}>{stats?.pending ?? 0} pending</span>
          </>
        }
        actions={headerActions}
      />

      <MetricStrip items={metricItems} />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <Surface padding="lg" radius="xl">
          <SectionHeader
            title="Operator controls"
            description="Trigger a run, pause submission, and keep the latest execution visible."
          />
          <div className="mt-5 flex flex-wrap gap-3">
            <Button
              loading={runNowMutation.isPending}
              disabled={operatorBusy}
              onClick={() => runNowMutation.mutate()}
              icon={<Play size={14} weight="bold" />}
            >
              Run now
            </Button>
            <Button
              variant="secondary"
              loading={pauseMutation.isPending}
              disabled={operatorBusy}
              onClick={() => pauseMutation.mutate()}
              icon={<Pause size={14} weight="bold" />}
            >
              Pause
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ["auto-apply-rules"] });
                queryClient.invalidateQueries({ queryKey: ["auto-apply-runs"] });
                queryClient.invalidateQueries({ queryKey: ["auto-apply-stats"] });
              }}
              icon={<ArrowClockwise size={14} weight="bold" />}
            >
              Refresh status
            </Button>
          </div>
        </Surface>

        <Surface padding="lg" radius="xl">
          <SectionHeader
            title="Latest run"
            description="Most recent execution attempt and queue posture."
          />
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <StateBlock
              tone={
                latestRun?.status === "failed"
                  ? "danger"
                  : latestRun?.status === "running" || stats?.pending
                    ? "warning"
                    : latestRun
                      ? "success"
                      : "muted"
              }
              icon={<Lightning size={18} weight="bold" />}
              title={latestRun ? latestRun.status : "Idle"}
              description={
                latestRun
                  ? `${latestRun.ats_provider ?? "Unknown ATS"} - ${Object.keys(latestRun.fields_filled ?? {}).length} fields filled`
                  : "No execution has been recorded yet."
              }
            />
            <StateBlock
              tone={stats?.pending ? "warning" : "success"}
              icon={<Clock size={18} weight="bold" />}
              title="Queue"
              description={
                stats?.pending
                  ? `${stats.pending} run${stats.pending === 1 ? "" : "s"} pending`
                  : "No runs waiting."
              }
            />
          </div>
          {latestRun ? (
            <div className="mt-4 rounded-none border-2 border-border bg-bg-tertiary p-4">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                Run details
              </div>
              <div className="mt-3 grid gap-3 text-sm text-text-secondary sm:grid-cols-2">
                <div>
                  <span className="font-semibold text-text-primary">Job</span>
                  <div className="mt-1 break-all">{latestRun.job_id}</div>
                </div>
                <div>
                  <span className="font-semibold text-text-primary">Missed fields</span>
                  <div className="mt-1">{latestRun.fields_missed.length || 0}</div>
                </div>
              </div>
              {latestRun.error_message ? (
                <p className="mt-3 text-sm leading-6 text-[var(--color-accent-danger)]">
                  {latestRun.error_message}
                </p>
              ) : null}
            </div>
          ) : null}
        </Surface>
      </div>

      <Tabs tabs={TABS.map((tab) => ({ ...tab }))} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "profiles" ? (
        <SplitWorkspace
          primary={
            <Surface padding="lg" radius="xl">
              <SectionHeader
                title="Profiles"
                description="Profiles carry contact fields and templates."
                action={
                  <Button
                    variant="secondary"
                    onClick={() => setShowCreateProfile(true)}
                    icon={<Plus size={14} weight="bold" />}
                  >
                    Add Profile
                  </Button>
                }
              />
              <div className="mt-5">
                {profilesLoading ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    {Array.from({ length: 2 }).map((_, index) => (
                      <SkeletonCard key={index} />
                    ))}
                  </div>
                ) : !profiles?.length ? (
                  <EmptyState
                    icon={<User size={40} weight="bold" />}
                    title="No profiles yet"
                    description="Create the first profile."
                    action={{ label: "Add Profile", onClick: () => setShowCreateProfile(true) }}
                  />
                ) : (
                  <div className="grid gap-4 lg:grid-cols-2">
                    {profiles.map((profile) => (
                      <ProfileCard key={profile.id} profile={profile} />
                    ))}
                  </div>
                )}
              </div>
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="success"
                icon={<Pulse size={18} weight="bold" />}
                title="Active profile"
                description={
                  profiles?.find((profile) => profile.is_active)
                    ? "Primary profile is active."
                    : "No active profile is marked yet."
                }
              />
              <StateBlock
                tone={latestRun?.status === "failed" ? "danger" : "warning"}
                icon={<Envelope size={18} weight="bold" />}
                title="Latest operator signal"
                description={
                  latestRun
                    ? `${latestRun.status} - ${Object.keys(latestRun.fields_filled ?? {}).length} fields filled`
                    : "Run the first batch to see field coverage."
                }
              />
            </div>
          }
        />
      ) : null}

      {activeTab === "rules" ? (
        <SplitWorkspace
          primary={
            <Surface padding="lg" radius="xl">
              <SectionHeader
                title="Rules"
                description="Rules gate which jobs can auto-submit."
                action={
                  <Button
                    variant="secondary"
                    onClick={() => setShowCreateRule(true)}
                    icon={<Plus size={14} weight="bold" />}
                  >
                    Add Rule
                  </Button>
                }
              />
              <div className="mt-5">
                {rulesLoading ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    {Array.from({ length: 2 }).map((_, index) => (
                      <SkeletonCard key={index} />
                    ))}
                  </div>
                ) : !rules?.length ? (
                  <EmptyState
                    icon={<Shield size={40} weight="bold" />}
                    title="No rules yet"
                    description="Create rules to gate automation."
                    action={{ label: "Add Rule", onClick: () => setShowCreateRule(true) }}
                  />
                ) : (
                  <div className="grid gap-4">
                    {rules.map((rule) => (
                      <RuleCard
                        key={rule.id}
                        rule={rule}
                        onToggleActive={() => toggleRuleMutation.mutate(rule)}
                      />
                    ))}
                  </div>
                )}
              </div>
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="neutral"
                icon={<ShieldCheck size={18} weight="bold" />}
                title="Rule logic"
                description="Required keywords shrink the pool. Excluded keywords block bad fits."
              />
              <StateBlock
                tone={stats?.pending ? "warning" : "danger"}
                icon={<Lightning size={18} weight="bold" />}
                title="Run posture"
                description={
                  stats?.pending
                    ? `${stats.pending} pending item${stats.pending === 1 ? "" : "s"} still in queue.`
                    : "If success drops, narrow active rules before adding profiles."
                }
              />
            </div>
          }
        />
      ) : null}

      {activeTab === "history" ? (
        <SplitWorkspace
          primary={
            <Surface padding="none" radius="xl" className="overflow-hidden">
              <div className="border-b-2 border-[var(--color-text-primary)] bg-bg-tertiary px-5 py-4">
                <SectionHeader
                  title="Run History"
                  description="Recent attempts and field coverage."
                />
              </div>
              {runsLoading ? (
                <div className="space-y-3 p-5">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <SkeletonCard key={index} />
                  ))}
                </div>
              ) : !runs?.length ? (
                <div className="p-5">
                  <EmptyState
                    icon={<Clock size={40} weight="bold" />}
                    title="No run history"
                    description="Runs will appear here after auto-apply starts."
                  />
                </div>
              ) : (
                <div>
                  {runs.map((run) => (
                    <RunRow key={run.id} run={run} />
                  ))}
                </div>
              )}
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="success"
                icon={<CheckCircle size={18} weight="bold" />}
                title="Success signal"
                description={`${stats?.successful ?? 0} completed runs are tracked.`}
              />
              <StateBlock
                tone="danger"
                icon={<XCircle size={18} weight="bold" />}
                title="Failure watch"
                description={
                  stats?.failed
                    ? `${stats.failed} runs failed. Inspect field coverage.`
                    : "No failed runs are currently recorded."
                }
              />
            </div>
          }
        />
      ) : null}

      {activeTab === "stats" ? (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
          <Surface padding="lg" radius="xl">
            <SectionHeader
              title="Summary"
              description="Automation volume, queue state, and execution quality."
            />
            {statsLoading ? (
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <SkeletonCard key={index} />
                ))}
              </div>
            ) : stats ? (
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                {[
                  {
                    label: "Total Runs",
                    value: stats.total_runs,
                    hint: "Attempts recorded end to end.",
                    icon: <Pulse size={18} weight="bold" />,
                  },
                  {
                    label: "Successful",
                    value: stats.successful,
                    hint: "Runs that completed cleanly.",
                    icon: <CheckCircle size={18} weight="bold" />,
                  },
                  {
                    label: "Failed",
                    value: stats.failed,
                    hint: "Runs requiring investigation.",
                    icon: <XCircle size={18} weight="bold" />,
                  },
                  {
                    label: "Pending",
                    value: stats.pending,
                    hint: "Items still in flight.",
                    icon: <Clock size={18} weight="bold" />,
                  },
                ].map((item) => (
                  <Surface key={item.label} tone="subtle" padding="md">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                          {item.label}
                        </div>
                        <div className="mt-3 text-4xl font-semibold tracking-[-0.06em] text-text-primary">
                          {item.value}
                        </div>
                        <p className="mt-2 text-sm leading-6 text-text-secondary">{item.hint}</p>
                      </div>
                      <div className="flex size-11 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-background">
                        {item.icon}
                      </div>
                    </div>
                  </Surface>
                ))}
              </div>
            ) : (
              <div className="mt-5">
                <EmptyState
                  icon={<ChartBar size={40} weight="bold" />}
                  title="No stats available"
                  description="Stats will appear once auto-apply starts processing jobs."
                />
              </div>
            )}
          </Surface>

          <div className="space-y-4">
            <StateBlock
              tone="warning"
              icon={<Lightning size={18} weight="bold" />}
              title="Queue health"
              description={
                stats?.pending
                  ? `There ${stats.pending === 1 ? "is" : "are"} ${stats.pending} pending application${stats.pending === 1 ? "" : "s"} in the queue.`
                  : "No items are waiting in the queue."
              }
            />
            <StateBlock
              tone="success"
              icon={<ShieldCheck size={18} weight="bold" />}
              title="Conversion"
              description={`Current success rate is ${successRate}% based on recorded runs.`}
            />
          </div>
        </div>
      ) : null}

      <CreateProfileModal open={showCreateProfile} onClose={() => setShowCreateProfile(false)} />
      <CreateRuleModal open={showCreateRule} onClose={() => setShowCreateRule(false)} />
    </div>
  );
}
