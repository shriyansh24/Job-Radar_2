import {
  ChartBar,
  CheckCircle,
  Clock,
  Envelope,
  Lightning,
  Plus,
  Pulse,
  Shield,
  ShieldCheck,
  User,
  X,
  XCircle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useMemo, useState } from "react";
import {
  autoApplyApi,
  type AutoApplyProfile,
  type AutoApplyProfileCreate,
  type AutoApplyRule,
  type AutoApplyRuleCreate,
  type AutoApplyRun,
} from "../api/auto-apply";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import { SkeletonCard } from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/toastService";
import { cn } from "../lib/utils";

const TABS = [
  { id: "profiles", label: "Profiles", icon: <User size={14} weight="bold" /> },
  { id: "rules", label: "Rules", icon: <Shield size={14} weight="bold" /> },
  { id: "history", label: "Run History", icon: <Clock size={14} weight="bold" /> },
  { id: "stats", label: "Statistics", icon: <ChartBar size={14} weight="bold" /> },
] as const;

const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";

const EMPTY_PROFILE: AutoApplyProfileCreate = {
  name: "",
  email: "",
  phone: "",
  linkedin_url: "",
  github_url: "",
  portfolio_url: "",
  cover_letter_template: "",
};

const EMPTY_RULE: AutoApplyRuleCreate = {
  name: "",
  min_match_score: undefined,
  required_keywords: [],
  excluded_keywords: [],
  is_active: true,
};

function statusVariant(status: string): "success" | "danger" | "warning" | "info" | "default" {
  switch (status) {
    case "completed":
      return "success";
    case "failed":
      return "danger";
    case "pending":
      return "warning";
    case "running":
      return "info";
    default:
      return "default";
  }
}

function ProfileCard({ profile }: { profile: AutoApplyProfile }) {
  return (
    <Surface tone="subtle" padding="md" className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold tracking-[-0.04em] text-text-primary">{profile.name}</h3>
            {profile.is_active ? <Badge variant="success">Active</Badge> : null}
          </div>
          <p className="mt-2 flex items-center gap-2 text-sm text-text-secondary">
            <Envelope size={14} weight="bold" />
            {profile.email}
          </p>
        </div>
        <div className="flex size-11 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-background">
          <User size={18} weight="bold" />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {profile.phone ? <span className={cn(CHIP, "bg-background text-text-primary")}>Phone</span> : null}
        {profile.linkedin_url ? (
          <span className={cn(CHIP, "bg-accent-primary/10 text-text-primary")}>LinkedIn</span>
        ) : null}
        {profile.github_url ? (
          <span className={cn(CHIP, "bg-accent-primary/10 text-text-primary")}>GitHub</span>
        ) : null}
        {profile.portfolio_url ? (
          <span className={cn(CHIP, "bg-accent-primary/10 text-text-primary")}>Portfolio</span>
        ) : null}
        {profile.cover_letter_template ? (
          <span className={cn(CHIP, "bg-accent-warning/10 text-text-primary")}>Template</span>
        ) : null}
      </div>
    </Surface>
  );
}

function RuleCard({
  rule,
  onToggleActive,
}: {
  rule: AutoApplyRule;
  onToggleActive: () => void;
}) {
  return (
    <Surface tone="subtle" padding="md" className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold tracking-[-0.04em] text-text-primary">{rule.name}</h3>
            <Badge variant={rule.is_active ? "success" : "default"}>
              {rule.is_active ? "Active" : "Inactive"}
            </Badge>
            {rule.min_match_score !== null ? (
              <span className={cn(CHIP, "bg-background text-text-primary")}>
                Match {rule.min_match_score}%
              </span>
            ) : null}
          </div>
          <div className="space-y-2">
            {rule.required_keywords.length ? (
              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Required
                </span>
                {rule.required_keywords.map((keyword) => (
                  <Badge key={keyword} variant="success" size="sm">
                    {keyword}
                  </Badge>
                ))}
              </div>
            ) : null}
            {rule.excluded_keywords.length ? (
              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                  Excluded
                </span>
                {rule.excluded_keywords.map((keyword) => (
                  <Badge key={keyword} variant="danger" size="sm">
                    {keyword}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={onToggleActive}
          icon={rule.is_active ? <ShieldCheck size={14} weight="bold" /> : <Shield size={14} weight="bold" />}
        >
          {rule.is_active ? "Deactivate" : "Activate"}
        </Button>
      </div>
    </Surface>
  );
}

function RunRow({ run }: { run: AutoApplyRun }) {
  return (
    <div className="border-t-2 border-[var(--color-text-primary)] px-4 py-4 first:border-t-0 sm:px-5">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1.2fr)_repeat(4,minmax(100px,1fr))]">
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">Job</div>
          <div className="mt-1 truncate text-sm font-semibold text-text-primary">{run.job_id.slice(0, 8)}...</div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">Status</div>
          <div className="mt-1">
            <Badge variant={statusVariant(run.status)} size="sm">
              {run.status}
            </Badge>
          </div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">ATS</div>
          <div className="mt-1 text-sm text-text-secondary">{run.ats_provider || "-"}</div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
            Fields Filled
          </div>
          <div className="mt-1 text-sm text-text-secondary">
            {Object.keys(run.fields_filled).length} filled
            {run.fields_missed.length ? (
              <span className="ml-1 text-accent-danger">({run.fields_missed.length} missed)</span>
            ) : null}
          </div>
        </div>
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">Time</div>
          <div className="mt-1 text-sm text-text-secondary">
            {run.completed_at
              ? format(new Date(run.completed_at), "PP p")
              : run.started_at
                ? format(new Date(run.started_at), "PP p")
                : "-"}
          </div>
        </div>
      </div>
    </div>
  );
}

function CreateProfileModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<AutoApplyProfileCreate>({ ...EMPTY_PROFILE });

  const mutation = useMutation({
    mutationFn: () => autoApplyApi.createProfile(form),
    onSuccess: () => {
      toast("success", "Profile created");
      queryClient.invalidateQueries({ queryKey: ["auto-apply-profiles"] });
      onClose();
      setForm({ ...EMPTY_PROFILE });
    },
    onError: () => toast("error", "Failed to create profile"),
  });

  return (
    <Modal open={open} onClose={onClose} title="Add Profile" size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Name"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="e.g. Default Profile"
          />
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            placeholder="e.g. john@example.com"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Phone"
            value={form.phone ?? ""}
            onChange={(event) => setForm({ ...form, phone: event.target.value })}
            placeholder="e.g. +1 555 123 4567"
          />
          <Input
            label="LinkedIn URL"
            value={form.linkedin_url ?? ""}
            onChange={(event) => setForm({ ...form, linkedin_url: event.target.value })}
            placeholder="e.g. https://linkedin.com/in/johndoe"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="GitHub URL"
            value={form.github_url ?? ""}
            onChange={(event) => setForm({ ...form, github_url: event.target.value })}
            placeholder="e.g. https://github.com/johndoe"
          />
          <Input
            label="Portfolio URL"
            value={form.portfolio_url ?? ""}
            onChange={(event) => setForm({ ...form, portfolio_url: event.target.value })}
            placeholder="e.g. https://johndoe.dev"
          />
        </div>
        <Textarea
          label="Cover Letter Template"
          value={form.cover_letter_template ?? ""}
          onChange={(event) => setForm({ ...form, cover_letter_template: event.target.value })}
          placeholder="Write a default cover letter template. Use {company} and {position} as placeholders..."
          rows={5}
        />
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            loading={mutation.isPending}
            disabled={!form.name || !form.email}
            onClick={() => mutation.mutate()}
          >
            Create Profile
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function KeywordInput({
  label,
  keywords,
  onChange,
  placeholder,
}: {
  label: string;
  keywords: string[];
  onChange: (keywords: string[]) => void;
  placeholder: string;
}) {
  const [inputValue, setInputValue] = useState("");

  function addKeyword() {
    const trimmed = inputValue.trim();
    if (!trimmed || keywords.includes(trimmed)) {
      return;
    }

    onChange([...keywords, trimmed]);
    setInputValue("");
  }

  function removeKeyword(keyword: string) {
    onChange(keywords.filter((value) => value !== keyword));
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-text-secondary">{label}</label>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          placeholder={placeholder}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addKeyword();
            }
          }}
        />
        <Button variant="secondary" size="md" onClick={addKeyword} disabled={!inputValue.trim()}>
          Add
        </Button>
      </div>
      {keywords.length ? (
        <div className="flex flex-wrap gap-2">
          {keywords.map((keyword) => (
            <span key={keyword} className={cn(CHIP, "bg-background text-text-primary")}>
              {keyword}
              <button
                type="button"
                onClick={() => removeKeyword(keyword)}
                className="inline-flex size-4 items-center justify-center border-l-2 border-[var(--color-text-primary)] pl-1 text-text-muted transition-colors hover:text-accent-danger"
              >
                <X size={10} weight="bold" />
              </button>
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function CreateRuleModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<AutoApplyRuleCreate>({ ...EMPTY_RULE });

  const mutation = useMutation({
    mutationFn: () => autoApplyApi.createRule(form),
    onSuccess: () => {
      toast("success", "Rule created");
      queryClient.invalidateQueries({ queryKey: ["auto-apply-rules"] });
      onClose();
      setForm({ ...EMPTY_RULE });
    },
    onError: () => toast("error", "Failed to create rule"),
  });

  return (
    <Modal open={open} onClose={onClose} title="Add Rule" size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Rule Name"
            value={form.name ?? ""}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="e.g. Senior Frontend Roles"
          />
          <Input
            label="Min Match Score (%)"
            type="number"
            min={0}
            max={100}
            value={form.min_match_score ?? ""}
            onChange={(event) =>
              setForm({
                ...form,
                min_match_score: event.target.value ? Number(event.target.value) : undefined,
              })
            }
            placeholder="e.g. 75"
          />
        </div>
        <KeywordInput
          label="Required Keywords"
          keywords={form.required_keywords ?? []}
          onChange={(keywords) => setForm({ ...form, required_keywords: keywords })}
          placeholder="e.g. React"
        />
        <KeywordInput
          label="Excluded Keywords"
          keywords={form.excluded_keywords ?? []}
          onChange={(keywords) => setForm({ ...form, excluded_keywords: keywords })}
          placeholder="e.g. Intern"
        />
        <label className="flex items-center gap-3 text-sm text-text-secondary">
          <input
            type="checkbox"
            className="size-4 border-2 border-border accent-[var(--color-accent-primary)]"
            checked={form.is_active ?? true}
            onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
          />
          Enable rule immediately
        </label>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            loading={mutation.isPending}
            disabled={!form.name}
            onClick={() => mutation.mutate()}
          >
            Create Rule
          </Button>
        </div>
      </div>
    </Modal>
  );
}

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

  const metricItems = useMemo(
    () => [
      {
        key: "profiles",
        label: "Profiles",
        value: profilesLoading ? "..." : String(profiles?.length ?? 0),
        hint: "Application identities ready to send.",
        tone: "default" as const,
      },
      {
        key: "rules",
        label: "Active Rules",
        value: rulesLoading ? "..." : String(activeRuleCount),
        hint: "Filters currently allowed to fire.",
        tone: "warning" as const,
      },
      {
        key: "runs",
        label: "Runs",
        value: statsLoading ? "..." : String(stats?.total_runs ?? 0),
        hint: "End-to-end automation attempts recorded.",
        tone: "success" as const,
      },
      {
        key: "success",
        label: "Success Rate",
        value: statsLoading ? "..." : `${successRate}%`,
        hint: "Share of runs that finished cleanly.",
        tone: "danger" as const,
      },
    ],
    [activeRuleCount, profiles?.length, profilesLoading, rulesLoading, stats, statsLoading, successRate]
  );

  const headerActions =
    activeTab === "profiles" ? (
      <Button onClick={() => setShowCreateProfile(true)} icon={<Plus size={16} weight="bold" />}>
        Add Profile
      </Button>
    ) : activeTab === "rules" ? (
      <Button onClick={() => setShowCreateRule(true)} icon={<Plus size={16} weight="bold" />}>
        Add Rule
      </Button>
    ) : null;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Execute"
        title="Auto Apply"
        description="Operate profiles, matching rules, and run history from one control surface. The layout stays dense on desktop and collapses to single-column lanes on tablet and phone."
        meta={
          <>
            <span className={cn(CHIP, "bg-bg-secondary text-text-primary")}>
              {profiles?.length ?? 0} profiles
            </span>
            <span className={cn(CHIP, "bg-bg-secondary text-text-primary")}>
              {activeRuleCount} active rules
            </span>
            <span className={cn(CHIP, "bg-bg-secondary text-text-primary")}>
              {stats?.pending ?? 0} pending
            </span>
          </>
        }
        actions={headerActions}
      />

      <MetricStrip items={metricItems} />

      <Tabs tabs={TABS.map((tab) => ({ ...tab }))} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "profiles" ? (
        <SplitWorkspace
          primary={
            <Surface padding="lg" radius="xl">
              <SectionHeader
                title="Profile roster"
                description="Each profile carries the contact fields and optional cover-letter template used during automation."
                action={
                  <Button variant="secondary" onClick={() => setShowCreateProfile(true)} icon={<Plus size={14} weight="bold" />}>
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
                    description="Create your first auto-apply profile with your contact details and cover letter template"
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
                    ? "Primary profile is marked active and ready for automation."
                    :
                  "No active profile is marked yet."
                }
              />
              <StateBlock
                tone="warning"
                icon={<Envelope size={18} weight="bold" />}
                title="Coverage"
                description="Add LinkedIn, GitHub, and a reusable template to reduce missed fields during submit flows."
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
                title="Rule stack"
                description="Rules gate which jobs are allowed to auto-submit. Keep them narrow enough to trust."
                action={
                  <Button variant="secondary" onClick={() => setShowCreateRule(true)} icon={<Plus size={14} weight="bold" />}>
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
                    description="Set up rules to automatically apply to jobs that match your criteria"
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
                title="How to read rules"
                description="Required keywords shrink the candidate pool. Excluded keywords are the fast guardrail against bad-fit automation."
              />
              <StateBlock
                tone="danger"
                icon={<Lightning size={18} weight="bold" />}
                title="Operating note"
                description="If success rate drops, narrow the active rule set before adding more profiles."
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
                  description="Recent execution attempts, ATS vendors, and field coverage."
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
                    description="Run history will appear here after auto-apply processes jobs"
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
                description={`${stats?.successful ?? 0} completed runs are currently tracked.`}
              />
              <StateBlock
                tone="danger"
                icon={<XCircle size={18} weight="bold" />}
                title="Failure watch"
                description={
                  stats?.failed
                    ? `${stats.failed} runs failed. Inspect ATS coverage and required fields.`
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
              description="A compact read of automation volume, queue state, and execution quality."
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
                  description="Stats will appear here once auto-apply starts processing jobs"
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
