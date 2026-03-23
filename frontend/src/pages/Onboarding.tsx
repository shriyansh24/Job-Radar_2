import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  Plus,
  Key,
  MagnifyingGlass,
  RocketLaunch,
  Sparkle,
  UserCircle,
  MapPin,
  CurrencyDollar,
} from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { profileApi } from "../api/profile";
import { settingsApi } from "../api/settings";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import { PageHeader } from "../components/system/PageHeader";
import { SettingsSection } from "../components/system/SettingsSection";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import { toast } from "../components/ui/toastService";

type StepId = 0 | 1 | 2 | 3;

const STEP_LABELS = ["Welcome", "Profile", "Search", "Integrations"] as const;
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

  const summaryItems = useMemo(
    () => [
      {
        key: "profile",
        label: "Profile",
        value: form.fullName || "Not set",
        hint: "The name used across the workspace.",
      },
      {
        key: "search",
        label: "Search seeds",
        value: form.searchQueries.length,
        hint: "Queries that shape discovery.",
      },
      {
        key: "companies",
        label: "Watchlist",
        value: form.watchlistCompanies.length,
        hint: "Target companies to track.",
      },
      {
        key: "integrations",
        label: "Keys",
        value: [form.openrouterKey, form.serpapiKey].filter(Boolean).length,
        hint: "Connections ready to sync.",
      },
    ],
    [form]
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
      if (items.includes(value)) return current;
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
        description="Set the profile, search seeds, and integrations that power the rest of the workspace. You can revisit all of this later from Settings."
        meta={
          <div className="flex flex-wrap gap-2">
            {STEP_LABELS.map((label, index) => (
              <Badge key={label} variant={index <= step ? "info" : "default"} size="sm">
                {label}
              </Badge>
            ))}
          </div>
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

      <SplitWorkspace
        primary={
          <Surface tone="default" padding="lg" radius="xl">
            <div className="space-y-6">
              {step === 0 ? (
                <div className="space-y-5">
                  <div className="flex items-center gap-3">
                    <div className="flex size-12 items-center justify-center rounded-[var(--radius-xl)] border border-border/70 bg-background/80">
                      <RocketLaunch size={24} weight="bold" className="text-[var(--color-accent-primary)]" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-semibold tracking-[-0.04em]">Welcome to Career OS</h2>
                      <p className="text-sm leading-6 text-muted-foreground">
                        This setup flow gives the system enough context to start discovering roles and
                        generating useful prep material.
                      </p>
                    </div>
                  </div>
                  <SettingsSection
                    title="What gets configured"
                    description="Identity, search targets, and integrations that make the rest of the product useful."
                  >
                    <div className="grid gap-3 md:grid-cols-3">
                      <StateBlock tone="muted" icon={<UserCircle size={18} weight="bold" />} title="Profile" />
                      <StateBlock tone="muted" icon={<MagnifyingGlass size={18} weight="bold" />} title="Search seeds" />
                      <StateBlock tone="muted" icon={<Key size={18} weight="bold" />} title="Integrations" />
                    </div>
                  </SettingsSection>
                </div>
              ) : null}

              {step === 1 ? (
                <SettingsSection
                  title="Profile"
                  description="Tell the workspace who you are and what kind of roles you want."
                >
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
                </SettingsSection>
              ) : null}

              {step === 2 ? (
                <SettingsSection
                  title="Search seeds"
                  description="These phrases and companies power discovery, alerts, and saved searches."
                >
                  <div className="space-y-4">
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
                </SettingsSection>
              ) : null}

              {step === 3 ? (
                <SettingsSection
                  title="Integrations"
                  description="Optional keys that unlock richer search and Copilot behavior."
                >
                  <div className="space-y-4">
                    {INTEGRATIONS.map((integration) => (
                      <div key={integration.provider} className="rounded-[var(--radius-xl)] border border-border/70 bg-background/80 p-4">
                        <div className="mb-2 flex items-center justify-between gap-3">
                          <div>
                            <div className="text-sm font-semibold tracking-[-0.01em]">{integration.label}</div>
                            <p className="mt-1 text-sm leading-6 text-muted-foreground">{integration.description}</p>
                          </div>
                        <Badge
                          variant={form[INTEGRATION_FIELDS[integration.provider]] ? "success" : "default"}
                          size="sm"
                        >
                          {form[INTEGRATION_FIELDS[integration.provider]] ? "Ready" : "Optional"}
                        </Badge>
                      </div>
                      <Input
                        label={`${integration.label} API key`}
                        type="password"
                        value={form[INTEGRATION_FIELDS[integration.provider]]}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            [INTEGRATION_FIELDS[integration.provider]]: event.target.value,
                          }))
                        }
                          placeholder={`Enter ${integration.label} key`}
                      />
                    </div>
                    ))}
                  </div>
                </SettingsSection>
              ) : null}

              <div className="flex items-center justify-between gap-3 border-t border-border/70 pt-4">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setStep((current) => Math.max(0, current - 1) as StepId)}
                  disabled={step === 0}
                  icon={<ArrowLeft size={16} weight="bold" />}
                >
                  Back
                </Button>
                <div className="flex items-center gap-3">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => navigate("/jobs", { replace: true })}
                >
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
            </div>
          </Surface>
        }
        secondary={
          <div className="space-y-4">
            {summaryItems.map((item) => (
              <StateBlock
                key={item.key}
                tone="neutral"
                title={item.label}
                description={`${item.value} · ${item.hint}`}
              />
            ))}
            <StateBlock
              tone="warning"
              icon={<Sparkle size={18} weight="bold" />}
              title="Tip"
              description="Complete onboarding with the fields you know now. Settings can refine everything later."
            />
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

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-muted-foreground">{label}</label>
      <div className="flex gap-2">
        <Input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              const trimmed = value.trim();
              if (!trimmed) return;
              onAdd(trimmed);
              setValue("");
            }
          }}
        />
                <Button
                  type="button"
                  variant="secondary"
                  icon={<Plus size={14} weight="bold" />}
                  onClick={() => {
            const trimmed = value.trim();
            if (!trimmed) return;
            onAdd(trimmed);
            setValue("");
          }}
        >
          Add
        </Button>
      </div>
      {items.length ? (
        <div className="flex flex-wrap gap-2">
              {items.map((item, index) => (
            <Badge key={`${item}-${index}`} variant="info" size="md">
              <span className="flex items-center gap-1.5">
                {item}
                <button type="button" onClick={() => onRemove(index)} className="hover:text-[var(--color-accent-danger)]">
                  <ArrowLeft size={10} weight="bold" />
                </button>
              </span>
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}
