import { ChartBar, Clock, Shield, User } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { autoApplyApi, type AutoApplyRule } from "../api/auto-apply";
import { AutoApplyPageHeaderActions } from "../components/auto-apply/AutoApplyPageHeaderActions";
import {
  AutoApplyLatestRunPanel,
  AutoApplyOperatorControlsPanel,
} from "../components/auto-apply/AutoApplyOperatorPanels";
import {
  AutoApplyHistoryTabPanel,
  AutoApplyProfilesTabPanel,
  AutoApplyRulesTabPanel,
  AutoApplyStatsTabPanel,
} from "../components/auto-apply/AutoApplyTabPanels";
import { CreateProfileModal } from "../components/auto-apply/CreateProfileModal";
import { CreateRuleModal } from "../components/auto-apply/CreateRuleModal";
import { CHIP } from "../components/auto-apply/autoApplyUtils";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import Tabs from "../components/ui/Tabs";
import { toast } from "../components/ui/toastService";
import { cn } from "../lib/utils";

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

  const refreshAutoApplyState = () => {
    queryClient.invalidateQueries({ queryKey: ["auto-apply-rules"] });
    queryClient.invalidateQueries({ queryKey: ["auto-apply-runs"] });
    queryClient.invalidateQueries({ queryKey: ["auto-apply-stats"] });
  };

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
        actions={
          <AutoApplyPageHeaderActions
            activeTab={activeTab}
            onRefresh={refreshAutoApplyState}
            onPause={() => pauseMutation.mutate()}
            onRun={() => runNowMutation.mutate()}
            onAddProfile={() => setShowCreateProfile(true)}
            onAddRule={() => setShowCreateRule(true)}
            pausePending={pauseMutation.isPending}
            runPending={runNowMutation.isPending}
            operatorBusy={operatorBusy}
          />
        }
      />

      <MetricStrip items={metricItems} />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <AutoApplyOperatorControlsPanel
          onRefresh={refreshAutoApplyState}
          onPause={() => pauseMutation.mutate()}
          onRun={() => runNowMutation.mutate()}
          pausePending={pauseMutation.isPending}
          runPending={runNowMutation.isPending}
          operatorBusy={operatorBusy}
        />
        <AutoApplyLatestRunPanel latestRun={latestRun} pendingCount={stats?.pending ?? 0} />
      </div>

      <Tabs tabs={TABS.map((tab) => ({ ...tab }))} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "profiles" ? (
        <AutoApplyProfilesTabPanel
          profiles={profiles}
          profilesLoading={profilesLoading}
          latestRun={latestRun}
          onShowCreateProfile={() => setShowCreateProfile(true)}
        />
      ) : null}

      {activeTab === "rules" ? (
        <AutoApplyRulesTabPanel
          rules={rules}
          rulesLoading={rulesLoading}
          pendingCount={stats?.pending ?? 0}
          onShowCreateRule={() => setShowCreateRule(true)}
          onToggleRule={(rule) => toggleRuleMutation.mutate(rule)}
        />
      ) : null}

      {activeTab === "history" ? (
        <AutoApplyHistoryTabPanel
          runs={runs}
          runsLoading={runsLoading}
          successfulCount={stats?.successful ?? 0}
          failedCount={stats?.failed ?? 0}
        />
      ) : null}

      {activeTab === "stats" ? (
        <AutoApplyStatsTabPanel
          stats={stats}
          statsLoading={statsLoading}
          successRate={successRate}
        />
      ) : null}

      <CreateProfileModal open={showCreateProfile} onClose={() => setShowCreateProfile(false)} />
      <CreateRuleModal open={showCreateRule} onClose={() => setShowCreateRule(false)} />
    </div>
  );
}
