import {
  BookOpen,
  Buildings,
  Envelope,
  FloppyDisk,
  GithubLogo,
  Globe,
  GraduationCap,
  LinkSimple,
  MagnifyingGlass,
  MapPin,
  Phone,
  Plus,
  Sparkle,
  UserCircle,
  X,
  CurrencyDollar,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { profileApi, type EducationEntry, type ExperienceEntry, type UserProfile } from "../api/profile";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import Textarea from "../components/ui/Textarea";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SettingsSection } from "../components/system/SettingsSection";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import { toast } from "../components/ui/toastService";
import { useAuthStore } from "../store/useAuthStore";

const JOB_TYPE_OPTIONS = [
  { value: "full_time", label: "Full-time" },
  { value: "part_time", label: "Part-time" },
  { value: "contract", label: "Contract" },
  { value: "freelance", label: "Freelance" },
  { value: "internship", label: "Internship" },
];

const REMOTE_TYPE_OPTIONS = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

const WORK_AUTH_OPTIONS = [
  { value: "", label: "Select..." },
  { value: "citizen", label: "US Citizen" },
  { value: "permanent_resident", label: "Permanent Resident" },
  { value: "h1b", label: "H-1B Visa" },
  { value: "opt", label: "OPT/CPT" },
  { value: "ead", label: "EAD" },
  { value: "other", label: "Other" },
];

const EMPTY_EDUCATION: EducationEntry = {
  school: "",
  degree: "",
  field: "",
  start_date: null,
  end_date: null,
};

const EMPTY_EXPERIENCE: ExperienceEntry = {
  company: "",
  title: "",
  start_date: null,
  end_date: null,
  description: null,
};

interface FormState {
  full_name: string;
  phone: string;
  location: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  work_authorization: string;
  preferred_job_types: string[];
  preferred_remote_types: string[];
  salary_min: string;
  salary_max: string;
  education: EducationEntry[];
  experience: ExperienceEntry[];
  search_queries: string[];
  search_locations: string[];
  watchlist_companies: string[];
  answer_bank: Record<string, string>;
}

function createInitialForm(profile?: UserProfile): FormState {
  return {
    full_name: profile?.full_name ?? "",
    phone: profile?.phone ?? "",
    location: profile?.location ?? "",
    linkedin_url: profile?.linkedin_url ?? "",
    github_url: profile?.github_url ?? "",
    portfolio_url: profile?.portfolio_url ?? "",
    work_authorization: profile?.work_authorization ?? "",
    preferred_job_types: profile?.preferred_job_types ?? [],
    preferred_remote_types: profile?.preferred_remote_types ?? [],
    salary_min: profile?.salary_min?.toString() ?? "",
    salary_max: profile?.salary_max?.toString() ?? "",
    education: profile?.education ?? [],
    experience: profile?.work_experience ?? [],
    search_queries: profile?.search_queries ?? [],
    search_locations: profile?.search_locations ?? [],
    watchlist_companies: profile?.watchlist_companies ?? [],
    answer_bank: profile?.answer_bank ?? {},
  };
}

function ToggleGroup({
  label,
  options,
  selected,
  onChange,
}: {
  label: string;
  options: { value: string; label: string }[];
  selected: string[];
  onChange: (values: string[]) => void;
}) {
  function toggle(value: string) {
    onChange(
      selected.includes(value)
        ? selected.filter((item) => item !== value)
        : [...selected, value]
    );
  }

  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-muted-foreground">{label}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => toggle(option.value)}
            className={
              selected.includes(option.value)
                ? "rounded-full border border-[var(--color-accent-primary)]/30 bg-[var(--color-accent-primary)]/10 px-3 py-1.5 text-sm font-medium text-[var(--color-accent-primary)]"
                : "rounded-full border border-border bg-background px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:border-border/90 hover:text-foreground"
            }
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function TagEditor({
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

  function addItem() {
    const trimmed = value.trim();
    if (!trimmed || items.includes(trimmed)) return;
    onAdd(trimmed);
    setValue("");
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-muted-foreground">{label}</label>
      <div className="flex gap-2">
        <Input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addItem();
            }
          }}
          placeholder={placeholder}
        />
        <Button type="button" variant="secondary" icon={<Plus size={14} weight="bold" />} onClick={addItem}>
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
                  <X size={12} weight="bold" />
                </button>
              </span>
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function EntryCard({
  title,
  children,
  onRemove,
}: {
  title: string;
  children: ReactNode;
  onRemove: () => void;
}) {
  return (
    <Surface tone="subtle" padding="md" radius="lg">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-foreground">{title}</div>
          <div className="mt-3">{children}</div>
        </div>
        <button type="button" onClick={onRemove} className="text-muted-foreground hover:text-[var(--color-accent-danger)]">
          <X size={16} weight="bold" />
        </button>
      </div>
    </Surface>
  );
}

export default function Profile() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.get().then((response) => response.data),
  });
  const [form, setForm] = useState<FormState>(createInitialForm());

  useEffect(() => {
    if (profile) {
      setForm(createInitialForm(profile));
    }
  }, [profile]);

  const saveMutation = useMutation({
    mutationFn: (data: Partial<UserProfile>) => profileApi.update(data),
    onSuccess: () => {
      toast("success", "Profile saved");
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
    onError: () => toast("error", "Failed to save profile"),
  });

  const answerMutation = useMutation({
    mutationFn: () => profileApi.generateAnswers(),
    onSuccess: () => {
      toast("success", "Answer bank generated");
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
    onError: () => toast("error", "Failed to generate answers"),
  });

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function saveProfile() {
    saveMutation.mutate({
      full_name: form.full_name || undefined,
      phone: form.phone || undefined,
      location: form.location || undefined,
      linkedin_url: form.linkedin_url || undefined,
      github_url: form.github_url || undefined,
      portfolio_url: form.portfolio_url || undefined,
      work_authorization: form.work_authorization || undefined,
      preferred_job_types: form.preferred_job_types,
      preferred_remote_types: form.preferred_remote_types,
      salary_min: form.salary_min ? Number(form.salary_min) : undefined,
      salary_max: form.salary_max ? Number(form.salary_max) : undefined,
      education: form.education,
      work_experience: form.experience,
      search_queries: form.search_queries,
      search_locations: form.search_locations,
      watchlist_companies: form.watchlist_companies,
      answer_bank: form.answer_bank,
    });
  }

  const metrics = [
    {
      key: "queries",
      label: "Search seeds",
      value: form.search_queries.length,
      hint: "Titles or phrases that shape discovery.",
    },
    {
      key: "watchlist",
      label: "Watchlist",
      value: form.watchlist_companies.length,
      hint: "Companies you want the system to track.",
    },
    {
      key: "education",
      label: "Education entries",
      value: form.education.length,
      hint: "Academic context used in prep surfaces.",
    },
    {
      key: "experience",
      label: "Experience entries",
      value: form.experience.length,
      hint: "Role history surfaced to Copilot and interview prep.",
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Prepare"
        title="Profile"
        description="Keep the source-of-truth profile here. This surface stores the identity, preference, and background data used across the rest of the workspace."
        actions={
          <>
            <Button
              variant="secondary"
              onClick={() => answerMutation.mutate()}
              loading={answerMutation.isPending}
              icon={<Sparkle size={16} weight="bold" />}
            >
              Generate answers
            </Button>
            <Button
              onClick={saveProfile}
              loading={saveMutation.isPending}
              icon={<FloppyDisk size={16} weight="bold" />}
            >
              Save profile
            </Button>
          </>
        }
      />

      <MetricStrip items={metrics} />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <SettingsSection
              title="Identity and links"
              description="The basics that every other surface references."
            >
              {isLoading ? (
                <div className="grid gap-4 md:grid-cols-2">
                  {Array.from({ length: 6 }).map((_, index) => (
                    <Skeleton key={index} variant="rect" className="h-12 w-full" />
                  ))}
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  <Input
                    label="Full name"
                    value={form.full_name}
                    onChange={(event) => updateField("full_name", event.target.value)}
                    placeholder="Jane Doe"
                    icon={<UserCircle size={16} weight="bold" />}
                  />
                  <Input
                    label="Email"
                    value={user?.email ?? ""}
                    disabled
                    icon={<Envelope size={16} weight="bold" />}
                  />
                  <Input
                    label="Phone"
                    value={form.phone}
                    onChange={(event) => updateField("phone", event.target.value)}
                    placeholder="+1 555 000 0000"
                    icon={<Phone size={16} weight="bold" />}
                  />
                  <Input
                    label="Location"
                    value={form.location}
                    onChange={(event) => updateField("location", event.target.value)}
                    placeholder="New York, NY"
                    icon={<MapPin size={16} weight="bold" />}
                  />
                  <Input
                    label="LinkedIn"
                    value={form.linkedin_url}
                    onChange={(event) => updateField("linkedin_url", event.target.value)}
                    placeholder="https://linkedin.com/in/..."
                    icon={<LinkSimple size={16} weight="bold" />}
                  />
                  <Input
                    label="GitHub"
                    value={form.github_url}
                    onChange={(event) => updateField("github_url", event.target.value)}
                    placeholder="https://github.com/..."
                    icon={<GithubLogo size={16} weight="bold" />}
                  />
                  <Input
                    label="Portfolio"
                    value={form.portfolio_url}
                    onChange={(event) => updateField("portfolio_url", event.target.value)}
                    placeholder="https://..."
                    icon={<Globe size={16} weight="bold" />}
                  />
                  <Select
                    label="Work authorization"
                    value={form.work_authorization}
                    onChange={(event) => updateField("work_authorization", event.target.value)}
                    options={WORK_AUTH_OPTIONS}
                  />
                </div>
              )}
            </SettingsSection>

            <SettingsSection
              title="Preferences"
              description="Job type, remote preference, and compensation bounds used throughout discovery."
            >
              <div className="space-y-5">
                <ToggleGroup
                  label="Preferred job types"
                  options={JOB_TYPE_OPTIONS}
                  selected={form.preferred_job_types}
                  onChange={(values) => updateField("preferred_job_types", values)}
                />
                <ToggleGroup
                  label="Preferred remote types"
                  options={REMOTE_TYPE_OPTIONS}
                  selected={form.preferred_remote_types}
                  onChange={(values) => updateField("preferred_remote_types", values)}
                />
                <div className="grid gap-4 md:grid-cols-2">
                  <Input
                    label="Salary minimum"
                    type="number"
                    value={form.salary_min}
                    onChange={(event) => updateField("salary_min", event.target.value)}
                    icon={<CurrencyDollar size={16} weight="bold" />}
                  />
                  <Input
                    label="Salary maximum"
                    type="number"
                    value={form.salary_max}
                    onChange={(event) => updateField("salary_max", event.target.value)}
                    icon={<CurrencyDollar size={16} weight="bold" />}
                  />
                </div>
              </div>
            </SettingsSection>

            <SettingsSection
              title="Search seeds"
              description="The initial phrases and target companies that inform discovery."
            >
              <div className="space-y-5">
                <TagEditor
                  label="Search queries"
                  placeholder="e.g. Senior frontend engineer"
                  items={form.search_queries}
                  onAdd={(value) => updateField("search_queries", [...form.search_queries, value])}
                  onRemove={(index) =>
                    updateField("search_queries", form.search_queries.filter((_, i) => i !== index))
                  }
                />
                <TagEditor
                  label="Search locations"
                  placeholder="e.g. Remote, New York"
                  items={form.search_locations}
                  onAdd={(value) => updateField("search_locations", [...form.search_locations, value])}
                  onRemove={(index) =>
                    updateField("search_locations", form.search_locations.filter((_, i) => i !== index))
                  }
                />
                <TagEditor
                  label="Watchlist companies"
                  placeholder="e.g. Stripe"
                  items={form.watchlist_companies}
                  onAdd={(value) =>
                    updateField("watchlist_companies", [...form.watchlist_companies, value])
                  }
                  onRemove={(index) =>
                    updateField("watchlist_companies", form.watchlist_companies.filter((_, i) => i !== index))
                  }
                />
              </div>
            </SettingsSection>

            <SettingsSection
              title="Education"
              description="A compact history of academic context used for matching and interview prep."
            >
              <div className="space-y-3">
                {form.education.map((entry, index) => (
                  <EntryCard
                    key={`${entry.school}-${index}`}
                    title={entry.school || `Education ${index + 1}`}
                    onRemove={() =>
                      updateField(
                        "education",
                        form.education.filter((_, itemIndex) => itemIndex !== index)
                      )
                    }
                  >
                    <div className="grid gap-3 md:grid-cols-3">
                      <Input
                        value={entry.school}
                        onChange={(event) => {
                          const next = [...form.education];
                          next[index] = { ...entry, school: event.target.value };
                          updateField("education", next);
                        }}
                        placeholder="School"
                      />
                      <Input
                        value={entry.degree}
                        onChange={(event) => {
                          const next = [...form.education];
                          next[index] = { ...entry, degree: event.target.value };
                          updateField("education", next);
                        }}
                        placeholder="Degree"
                      />
                      <Input
                        value={entry.field}
                        onChange={(event) => {
                          const next = [...form.education];
                          next[index] = { ...entry, field: event.target.value };
                          updateField("education", next);
                        }}
                        placeholder="Field"
                      />
                    </div>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <Input
                        value={entry.start_date ?? ""}
                        onChange={(event) => {
                          const next = [...form.education];
                          next[index] = { ...entry, start_date: event.target.value || null };
                          updateField("education", next);
                        }}
                        placeholder="Start date"
                      />
                      <Input
                        value={entry.end_date ?? ""}
                        onChange={(event) => {
                          const next = [...form.education];
                          next[index] = { ...entry, end_date: event.target.value || null };
                          updateField("education", next);
                        }}
                        placeholder="End date"
                      />
                    </div>
                  </EntryCard>
                ))}
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => updateField("education", [...form.education, { ...EMPTY_EDUCATION }])}
                  icon={<Plus size={14} weight="bold" />}
                >
                  Add education
                </Button>
              </div>
            </SettingsSection>

            <SettingsSection
              title="Experience"
              description="Role history shown in prepare and intelligence surfaces."
            >
              <div className="space-y-3">
                {form.experience.map((entry, index) => (
                  <EntryCard
                    key={`${entry.company}-${index}`}
                    title={entry.company || `Role ${index + 1}`}
                    onRemove={() =>
                      updateField(
                        "experience",
                        form.experience.filter((_, itemIndex) => itemIndex !== index)
                      )
                    }
                  >
                    <div className="grid gap-3 md:grid-cols-2">
                      <Input
                        value={entry.company}
                        onChange={(event) => {
                          const next = [...form.experience];
                          next[index] = { ...entry, company: event.target.value };
                          updateField("experience", next);
                        }}
                        placeholder="Company"
                      />
                      <Input
                        value={entry.title}
                        onChange={(event) => {
                          const next = [...form.experience];
                          next[index] = { ...entry, title: event.target.value };
                          updateField("experience", next);
                        }}
                        placeholder="Title"
                      />
                    </div>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <Input
                        value={entry.start_date ?? ""}
                        onChange={(event) => {
                          const next = [...form.experience];
                          next[index] = { ...entry, start_date: event.target.value || null };
                          updateField("experience", next);
                        }}
                        placeholder="Start date"
                      />
                      <Input
                        value={entry.end_date ?? ""}
                        onChange={(event) => {
                          const next = [...form.experience];
                          next[index] = { ...entry, end_date: event.target.value || null };
                          updateField("experience", next);
                        }}
                        placeholder="End date or Present"
                      />
                    </div>
                    <Textarea
                      className="mt-3 min-h-[110px]"
                      value={entry.description ?? ""}
                      onChange={(event) => {
                        const next = [...form.experience];
                        next[index] = { ...entry, description: event.target.value || null };
                        updateField("experience", next);
                      }}
                      placeholder="What you owned, shipped, or learned."
                    />
                  </EntryCard>
                ))}
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => updateField("experience", [...form.experience, { ...EMPTY_EXPERIENCE }])}
                  icon={<Plus size={14} weight="bold" />}
                >
                  Add experience
                </Button>
              </div>
            </SettingsSection>

            <SettingsSection
              title="Answer bank"
              description="Reusable interview answers generated from the current profile."
              actions={
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => answerMutation.mutate()}
                  loading={answerMutation.isPending}
                  icon={<Sparkle size={16} weight="bold" />}
                >
                  Generate
                </Button>
              }
            >
              <div className="space-y-4">
                {Object.keys(form.answer_bank).length ? (
                  Object.entries(form.answer_bank).map(([question, answer]) => (
                    <div key={question} className="space-y-2">
                      <div className="flex items-center justify-between gap-3">
                        <label className="text-sm font-medium text-foreground">{question}</label>
                        <button
                          type="button"
                          onClick={() => {
                            const next = { ...form.answer_bank };
                            delete next[question];
                            updateField("answer_bank", next);
                          }}
                          className="text-muted-foreground hover:text-[var(--color-accent-danger)]"
                        >
                          <X size={14} weight="bold" />
                        </button>
                      </div>
                      <Textarea
                        value={answer}
                        onChange={(event) =>
                          updateField("answer_bank", {
                            ...form.answer_bank,
                            [question]: event.target.value,
                          })
                        }
                        className="min-h-[100px]"
                      />
                    </div>
                  ))
                ) : (
                  <StateBlock
                    tone="muted"
                    icon={<BookOpen size={18} weight="bold" />}
                    title="No answers yet"
                    description='Generate them from the resume/profile source of truth or add your own manually.'
                  />
                )}
              </div>
            </SettingsSection>
          </div>
        }
        secondary={
          <div className="space-y-4">
            <StateBlock
              tone="neutral"
              icon={<MagnifyingGlass size={18} weight="bold" />}
              title="Profile usage"
              description="Discovery, onboarding, interview prep, and Copilot all read from this record."
            />
            <StateBlock
              tone="success"
              icon={<Buildings size={18} weight="bold" />}
              title="Workspace summary"
              description={`${form.watchlist_companies.length} watchlist companies and ${form.search_queries.length} search seeds currently configured.`}
            />
            <StateBlock
              tone="warning"
              icon={<GraduationCap size={18} weight="bold" />}
              title="Readiness check"
              description="Add at least one role and one search seed to make the other surfaces immediately useful."
            />
          </div>
        }
      />
    </div>
  );
}
