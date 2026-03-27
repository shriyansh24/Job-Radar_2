import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Key, MagnifyingGlass, UserCircle } from "@phosphor-icons/react";
import { profileApi } from "../api/profile";
import { settingsApi } from "../api/settings";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Button from "../components/ui/Button";
import { toast } from "../components/ui/toastService";
import { OnboardingHeroPanel } from "../components/onboarding/OnboardingHeroPanel";
import { OnboardingIntegrationsStep } from "../components/onboarding/OnboardingIntegrationsStep";
import { OnboardingProfileStep } from "../components/onboarding/OnboardingProfileStep";
import { OnboardingSearchStep } from "../components/onboarding/OnboardingSearchStep";
import { OnboardingSummaryRail } from "../components/onboarding/OnboardingSummaryRail";

type StepId = 0 | 1 | 2 | 3;

const STEP_LABELS = ["Welcome", "Profile", "Search", "Integrations"] as const;

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
        description="Seed identity, search handles, and integrations so the workspace starts with enough context."
        meta={
          <>
            {STEP_LABELS.map((label, index) => (
              <span
                key={label}
                className={`border-2 px-3 py-2 text-[10px] font-bold uppercase tracking-[0.16em] ${
                  index <= step
                    ? "border-[var(--color-text-primary)] bg-accent-primary text-white"
                    : "border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] text-text-muted"
                }`}
              >
                {label}
              </span>
            ))}
          </>
        }
        actions={
          <Button onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>
            Finish setup
          </Button>
        }
      />

      <MetricStrip items={metricItems} />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <OnboardingHeroPanel
              step={step}
              stepLabels={STEP_LABELS}
              title={activeStep.title}
              description={activeStep.description}
              callout={activeStep.callout}
              profileName={form.fullName}
              searchCount={form.searchQueries.length}
            />

            <Surface padding="lg" radius="xl">
              {step === 0 ? (
                <div className="space-y-6">
                  <SectionHeader
                    title="What gets configured"
                    description="A few high-value fields are enough to start discovery, prep, and follow-up."
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
                <OnboardingProfileStep
                  fullName={form.fullName}
                  location={form.location}
                  salaryMin={form.salaryMin}
                  salaryMax={form.salaryMax}
                  preferredJobTypes={form.preferredJobTypes}
                  preferredRemoteTypes={form.preferredRemoteTypes}
                  onChange={(patch) => setForm((current) => ({ ...current, ...patch }))}
                />
              ) : null}

              {step === 2 ? (
                <OnboardingSearchStep
                  searchQueries={form.searchQueries}
                  searchLocations={form.searchLocations}
                  watchlistCompanies={form.watchlistCompanies}
                  onAdd={addItem}
                  onRemove={removeItem}
                />
              ) : null}

              {step === 3 ? (
                <OnboardingIntegrationsStep
                  fullName={form.fullName}
                  openrouterKey={form.openrouterKey}
                  serpapiKey={form.serpapiKey}
                  onChange={(patch) => setForm((current) => ({ ...current, ...patch }))}
                />
              ) : null}
            </Surface>

            <Surface padding="md" radius="xl">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setStep((current) => Math.max(0, current - 1) as StepId)}
                  disabled={step === 0}
                >
                  Back
                </Button>
                <div className="flex flex-wrap items-center gap-3">
                  <Button type="button" variant="ghost" onClick={() => navigate("/jobs", { replace: true })}>
                    Skip for now
                  </Button>
                  {step < 3 ? (
                    <Button type="button" onClick={() => setStep((current) => (current + 1) as StepId)}>
                      Next
                    </Button>
                  ) : (
                    <Button type="button" onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>
                      Finish
                    </Button>
                  )}
                </div>
              </div>
            </Surface>
          </div>
        }
        secondary={
          <OnboardingSummaryRail summaryItems={summaryItems} stepLabel={STEP_LABELS[step]} callout={activeStep.callout} />
        }
      />
    </div>
  );
}
