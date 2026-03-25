import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  CurrencyDollar,
  Key,
  MagnifyingGlass,
  MapPin,
  Plus,
  RocketLaunch,
  Sparkle,
  UserCircle,
  X,
} from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { profileApi } from "../api/profile";
import { settingsApi } from "../api/settings";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import { toast } from "../components/ui/toastService";
import { cn } from "../lib/utils";

type StepId = 0 | 1 | 2 | 3;

const STEP_LABELS = ["Welcome", "Profile", "Search", "Integrations"] as const;
const PANEL = "border-2 border-[var(--color-text-primary)] bg-bg-secondary shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const PANEL_SUBTLE =
  "border-2 border-[var(--color-text-primary)] bg-bg-tertiary shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";

const JOB_TYPE_OPTIONS = [
  { value: "full_time", label: "Full-time" },
  { value: "part_time", label: "Part-time" },
  { value: "contract", label: "Contract" },
  { value: "freelance", label: "Freelance" },
  { value: "internship", label: "Internship" },
];

const REMOTE_OPTIONS = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

const STEP_GUIDANCE = [
  {
    title: "Boot the workspace",
    description:
      "Start with just enough context for the system to route jobs, prep, and follow-up work into the right surfaces.",
    callout: "Nothing here is permanent. Settings can refine every field later.",
  },
  {
    title: "Shape the profile",
    description:
      "Capture who you are, where you want to work, and the salary band that sets your floor.",
    callout: "A lightweight profile makes downstream matching less noisy.",
  },
  {
    title: "Seed discovery",
    description:
      "Add the job titles, locations, and target companies that should drive job collection and ranking.",
    callout: "Think in search handles, not long prose.",
  },
  {
    title: "Connect engines",
    description:
      "Optional keys unlock richer search expansion and better Copilot drafting inside the workspace.",
    callout: "Leave keys blank if you do not have them yet.",
  },
] as const;

const INTEGRATIONS = [
  {
    provider: "openrouter" as const,
    label: "OpenRouter",
    description: "AI drafting, summarization, and interview prep.",
  },
  {
    provider: "serpapi" as const,
    label: "SerpAPI",
    description: "Broader search coverage for discovery.",
  },
];

const INTEGRATION_FIELDS = {
  openrouter: "openrouterKey",
  serpapi: "serpapiKey",
} as const;

function emptyState() {
  return {
    fullName: "",
    location: "",
    salaryMin: "",
    salaryMax: "",
    searchQueries: [] as string[],
    searchLocations: [] as string[],
    watchlistCompanies: [] as string[],
    openrouterKey: "",
    serpapiKey: "",
    preferredJobTypes: [] as string[],
    preferredRemoteTypes: [] as string[],
  };
}

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState<StepId>(0);
  const [form, setForm] = useState(emptyState);
  const activeStep = STEP_GUIDANCE[step];

  const summaryItems = useMemo(
    () => [
      {
        key: "profile",
        label: "Profile",
        value: form.fullName || "Not set",
        hint: "Identity used throughout the workspace.",
      },
      {
        key: "search",
        label: "Search seeds",
        value: form.searchQueries.length,
        hint: "Titles already shaping discovery.",
      },
      {
        key: "companies",
        label: "Watchlist",
        value: form.watchlistCompanies.length,
        hint: "Companies tracked across feeds and prep.",
      },
      {
        key: "integrations",
        label: "Connections",
        value: [form.openrouterKey, form.serpapiKey].filter(Boolean).length,
        hint: "External engines ready to use.",
      },
    ],
    [form]
  );

  const metricItems = useMemo(
    () => [
      {
        key: "completion",
        label: "Completion",
        value: `${Math.round(((step + 1) / STEP_LABELS.length) * 100)}%`,
        hint: "Progress through the first-run setup.",
        tone: "default" as const,
      },
      {
        key: "queries",
        label: "Queries",
        value: form.searchQueries.length.toString(),
        hint: "Primary job-title handles.",
        tone: "warning" as const,
      },
      {
        key: "locations",
        label: "Locations",
        value: form.searchLocations.length.toString(),
        hint: "Places or remote modes to watch.",
        tone: "success" as const,
      },
      {
        key: "keys",
        label: "Keys Ready",
        value: [form.openrouterKey, form.serpapiKey].filter(Boolean).length.toString(),
        hint: "Optional integrations connected.",
        tone: "danger" as const,
      },
    ],
    [form, step]
  );

  const saveMutation = useMutation({
    mutationFn: async () => {
      await profileApi.update({
        full_name: form.fullName || null,
        location: form.location || null,
        salary_min: form.salaryMin ? Number(form.salaryMin) : null,
        salary_max: form.salaryMax ? Number(form.salaryMax) : null,
        search_queries: form.searchQueries,
        search_locations: form.searchLocations,
        watchlist_companies: form.watchlistCompanies,
        preferred_job_types: form.preferredJobTypes,
        preferred_remote_types: form.preferredRemoteTypes,
      });

      const tasks: Promise<unknown>[] = [];
      if (form.openrouterKey.trim()) {
        tasks.push(settingsApi.upsertIntegration("openrouter", form.openrouterKey.trim()));
      }
      if (form.serpapiKey.trim()) {
        tasks.push(settingsApi.upsertIntegration("serpapi", form.serpapiKey.trim()));
      }

      await Promise.all(tasks);
    },
    onSuccess: () => {
      toast("success", "Workspace seeded");
      navigate("/jobs", { replace: true });
    },
    onError: () => toast("error", "Failed to finish onboarding"),
  });

  function addItem(key: "searchQueries" | "searchLocations" | "watchlistCompanies", value: string) {
    setForm((current) => {
      const items = current[key];
      if (items.includes(value)) {
        return current;
      }

      return { ...current, [key]: [...items, value] };
    });
  }

  function removeItem(key: "searchQueries" | "searchLocations" | "watchlistCompanies", index: number) {
    setForm((current) => ({
      ...current,
      [key]: current[key].filter((_, itemIndex) => itemIndex !== index),
    }));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="First-run setup"
        title="Onboarding"
        description="Seed identity, search handles, and integrations so the new workspace starts with enough context to discover roles and draft useful material."
        meta={
          <>
            {STEP_LABELS.map((label, index) => (
              <span
                key={label}
                className={cn(
                  CHIP,
                  index <= step ? "bg-accent-primary text-white" : "bg-bg-secondary text-text-muted"
                )}
              >
                {label}
              </span>
            ))}
          </>
        }
        actions={
          <Button
            onClick={() => saveMutation.mutate()}
            loading={saveMutation.isPending}
            icon={<CheckCircle size={16} weight="bold" />}
          >
            Finish setup
          </Button>
        }
      />

      <MetricStrip items={metricItems} />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <section className={cn(PANEL, "overflow-hidden")}>
              <div className="grid gap-0 lg:grid-cols-[minmax(0,1.5fr)_minmax(260px,0.85fr)]">
                <div className="p-5 sm:p-6 lg:p-8">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={CHIP}>Step {step + 1}</span>
                    <span className={CHIP}>{STEP_LABELS[step]}</span>
                  </div>
                  <div className="mt-5 flex items-start gap-4">
                    <div className="flex size-14 shrink-0 items-center justify-center border-2 border-[var(--color-text-primary)] bg-bg-tertiary">
                      <RocketLaunch size={28} weight="bold" />
                    </div>
                    <div className="space-y-3">
                      <h2 className="text-3xl font-semibold tracking-[-0.06em] text-text-primary sm:text-4xl">
                        {activeStep.title}
                      </h2>
                      <p className="max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
                        {activeStep.description}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border-t-2 border-[var(--color-text-primary)] bg-bg-tertiary p-5 sm:p-6 lg:border-l-2 lg:border-t-0">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">
                    Step signal
                  </div>
                  <div className="mt-3 h-4 border-2 border-[var(--color-text-primary)] bg-background">
                    <div
                      className="h-full bg-accent-primary transition-[width] duration-[var(--transition-normal)]"
                      style={{ width: `${((step + 1) / STEP_LABELS.length) * 100}%` }}
                    />
                  </div>
                  <p className="mt-4 text-sm leading-6 text-text-secondary">{activeStep.callout}</p>
                  <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
                    <StateBlock
                      tone="muted"
                      icon={<UserCircle size={18} weight="bold" />}
                      title="Identity"
                      description={form.fullName || "No name captured yet."}
                    />
                    <StateBlock
                      tone="warning"
                      icon={<MagnifyingGlass size={18} weight="bold" />}
                      title="Discovery"
                      description={
                        form.searchQueries.length
                          ? `${form.searchQueries.length} title seeds queued.`
                          : "Add titles and companies next."
                      }
                    />
                  </div>
                </div>
              </div>
            </section>

            <Surface padding="lg" radius="xl">
              {step === 0 ? (
                <div className="space-y-6">
                  <SectionHeader
                    title="What gets configured"
                    description="The system only needs a few high-value fields to start operating correctly across discovery, prep, and follow-up."
                  />
                  <div className="grid gap-4 md:grid-cols-3">
                    <StateBlock
                      tone="muted"
                      icon={<UserCircle size={18} weight="bold" />}
                      title="Profile"
                      description="The identity and salary frame behind every match."
                    />
                    <StateBlock
                      tone="warning"
                      icon={<MagnifyingGlass size={18} weight="bold" />}
                      title="Search seeds"
                      description="The queries, locations, and watchlist that shape the feed."
                    />
                    <StateBlock
                      tone="success"
                      icon={<Key size={18} weight="bold" />}
                      title="Integrations"
                      description="Optional engines that broaden search and drafting."
                    />
                  </div>
                </div>
              ) : null}

              {step === 1 ? (
                <div className="space-y-6">
                  <SectionHeader
                    title="Profile"
                    description="Tell the workspace who you are, which roles you want, and the compensation band that defines a serious opportunity."
                  />
                  <div className="grid gap-4 md:grid-cols-2">
                    <Input
                      label="Full name"
                      value={form.fullName}
                      onChange={(event) => setForm((current) => ({ ...current, fullName: event.target.value }))}
                      placeholder="Jane Doe"
                      icon={<UserCircle size={16} weight="bold" />}
                    />
                    <Input
                      label="Location"
                      value={form.location}
                      onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))}
                      placeholder="New York, NY"
                      icon={<MapPin size={16} weight="bold" />}
                    />
                    <Select
                      label="Preferred job types"
                      value={form.preferredJobTypes[0] ?? ""}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          preferredJobTypes: event.target.value ? [event.target.value] : [],
                        }))
                      }
                      options={JOB_TYPE_OPTIONS}
                      placeholder="Select a primary job type"
                    />
                    <Select
                      label="Preferred remote type"
                      value={form.preferredRemoteTypes[0] ?? ""}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          preferredRemoteTypes: event.target.value ? [event.target.value] : [],
                        }))
                      }
                      options={REMOTE_OPTIONS}
                      placeholder="Select a primary remote type"
                    />
                    <Input
                      label="Salary minimum"
                      type="number"
                      value={form.salaryMin}
                      onChange={(event) => setForm((current) => ({ ...current, salaryMin: event.target.value }))}
                      icon={<CurrencyDollar size={16} weight="bold" />}
                    />
                    <Input
                      label="Salary maximum"
                      type="number"
                      value={form.salaryMax}
                      onChange={(event) => setForm((current) => ({ ...current, salaryMax: event.target.value }))}
                      icon={<CurrencyDollar size={16} weight="bold" />}
                    />
                  </div>
                </div>
              ) : null}

              {step === 2 ? (
                <div className="space-y-6">
                  <SectionHeader
                    title="Search seeds"
                    description="Feed the discover surface with compact handles rather than long descriptions. The system can expand from there."
                  />
                  <div className="space-y-5">
                    <TagRow
                      label="Job titles"
                      placeholder="Software Engineer"
                      items={form.searchQueries}
                      onAdd={(value) => addItem("searchQueries", value)}
                      onRemove={(index) => removeItem("searchQueries", index)}
                    />
                    <TagRow
                      label="Locations"
                      placeholder="Remote"
                      items={form.searchLocations}
                      onAdd={(value) => addItem("searchLocations", value)}
                      onRemove={(index) => removeItem("searchLocations", index)}
                    />
                    <TagRow
                      label="Watchlist companies"
                      placeholder="Stripe"
                      items={form.watchlistCompanies}
                      onAdd={(value) => addItem("watchlistCompanies", value)}
                      onRemove={(index) => removeItem("watchlistCompanies", index)}
                    />
                  </div>
                </div>
              ) : null}

              {step === 3 ? (
                <div className="space-y-6">
                  <SectionHeader
                    title="Integrations"
                    description="Optional keys unlock broader search coverage and stronger drafting. Leave them blank if you want to finish setup first."
                  />
                  <form className="grid gap-4" onSubmit={(event) => event.preventDefault()}>
                    <input
                      type="text"
                      name="integration-username"
                      autoComplete="username"
                      value={form.fullName || "onboarding"}
                      readOnly
                      tabIndex={-1}
                      aria-hidden="true"
                      className="sr-only"
                    />
                    {INTEGRATIONS.map((integration) => {
                      const fieldKey = INTEGRATION_FIELDS[integration.provider];
                      const connected = Boolean(form[fieldKey]);

                      return (
                        <div key={integration.provider} className={cn(PANEL_SUBTLE, "p-4 sm:p-5")}>
                          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                            <div className="space-y-2">
                              <div className="flex items-center gap-2">
                                <span className={CHIP}>{integration.label}</span>
                                <Badge variant={connected ? "success" : "default"} size="sm">
                                  {connected ? "Ready" : "Optional"}
                                </Badge>
                              </div>
                              <p className="text-sm leading-6 text-text-secondary">
                                {integration.description}
                              </p>
                            </div>
                            <div className="min-w-0 flex-1 lg:max-w-md">
                              <Input
                                label={`${integration.label} API key`}
                                type="password"
                                autoComplete="off"
                                name={`${integration.provider}-api-key`}
                                value={form[fieldKey]}
                                onChange={(event) =>
                                  setForm((current) => ({
                                    ...current,
                                    [fieldKey]: event.target.value,
                                  }))
                                }
                                placeholder={`Enter ${integration.label} key`}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </form>
                </div>
              ) : null}
            </Surface>

            <Surface padding="md" radius="xl">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setStep((current) => Math.max(0, current - 1) as StepId)}
                  disabled={step === 0}
                  icon={<ArrowLeft size={16} weight="bold" />}
                >
                  Back
                </Button>
                <div className="flex flex-wrap items-center gap-3">
                  <Button type="button" variant="ghost" onClick={() => navigate("/jobs", { replace: true })}>
                    Skip for now
                  </Button>
                  {step < 3 ? (
                    <Button
                      type="button"
                      onClick={() => setStep((current) => (current + 1) as StepId)}
                      icon={<ArrowRight size={16} weight="bold" />}
                    >
                      Next
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      onClick={() => saveMutation.mutate()}
                      loading={saveMutation.isPending}
                      icon={<CheckCircle size={16} weight="bold" />}
                    >
                      Finish
                    </Button>
                  )}
                </div>
              </div>
            </Surface>
          </div>
        }
        secondary={
          <div className="space-y-4">
            {summaryItems.map((item) => (
              <StateBlock
                key={item.key}
                tone="neutral"
                title={item.label}
                description={`${item.value} - ${item.hint}`}
              />
            ))}
            <Surface padding="lg" radius="xl">
              <SectionHeader
                title="Current move"
                description={`You are on ${STEP_LABELS[step]}. Finish with what you know now and tune later from Settings.`}
              />
              <div className="mt-4 space-y-3">
                <StateBlock
                  tone="warning"
                  icon={<Sparkle size={18} weight="bold" />}
                  title="Guidance"
                  description={activeStep.callout}
                />
                <StateBlock
                  tone="success"
                  icon={<RocketLaunch size={18} weight="bold" />}
                  title="Outcome"
                  description="A completed setup immediately unlocks job discovery, saved filters, and better prep surfaces."
                />
              </div>
            </Surface>
          </div>
        }
      />
    </div>
  );
}

function TagRow({
  label,
  placeholder,
  items,
  onAdd,
  onRemove,
}: {
  label: string;
  placeholder: string;
  items: string[];
  onAdd: (value: string) => void;
  onRemove: (index: number) => void;
}) {
  const [value, setValue] = useState("");

  function commitValue() {
    const trimmed = value.trim();
    if (!trimmed) {
      return;
    }

    onAdd(trimmed);
    setValue("");
  }

  return (
    <div className={cn(PANEL_SUBTLE, "p-4 sm:p-5")}>
      <div className="flex flex-col gap-4">
        <div className="space-y-1">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-muted">{label}</div>
          <p className="text-sm leading-6 text-text-secondary">
            Add concise handles. One strong seed is better than a paragraph.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder={placeholder}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                commitValue();
              }
            }}
          />
          <Button type="button" variant="secondary" icon={<Plus size={14} weight="bold" />} onClick={commitValue}>
            Add
          </Button>
        </div>

        {items.length ? (
          <div className="flex flex-wrap gap-2">
            {items.map((item, index) => (
              <span key={`${item}-${index}`} className={cn(CHIP, "bg-bg-secondary text-text-primary")}>
                {item}
                <button
                  type="button"
                  onClick={() => onRemove(index)}
                  className="inline-flex size-4 items-center justify-center border-l-2 border-[var(--color-text-primary)] pl-1 text-text-muted transition-colors hover:text-accent-danger"
                  aria-label={`Remove ${item}`}
                >
                  <X size={10} weight="bold" />
                </button>
              </span>
            ))}
          </div>
        ) : (
          <div className="border-2 border-dashed border-[var(--color-text-primary)] bg-background px-4 py-5 text-sm text-text-muted">
            No entries yet.
          </div>
        )}
      </div>
    </div>
  );
}
