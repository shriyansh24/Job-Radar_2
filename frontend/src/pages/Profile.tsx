import {
  Briefcase,
  GithubLogo,
  Globe,
  GraduationCap,
  LinkSimple,
  MagnifyingGlass,
  MapPin,
  Buildings,
  BookOpen,
  CurrencyDollar,
  Envelope,
  FloppyDisk,
  Plus,
  Phone,
  Sparkle,
  UserCircle,
  X,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { profileApi, type EducationEntry, type ExperienceEntry, type UserProfile } from "../api/profile";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import { toast } from "../components/ui/toastService";
import { useAuthStore } from "../store/useAuthStore";

const JOB_TYPE_OPTIONS = [
  { value: 'full_time', label: 'Full-time' },
  { value: 'part_time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'freelance', label: 'Freelance' },
  { value: 'internship', label: 'Internship' },
];

const REMOTE_TYPE_OPTIONS = [
  { value: 'remote', label: 'Remote' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'onsite', label: 'On-site' },
];

const WORK_AUTH_OPTIONS = [
  { value: '', label: 'Select...' },
  { value: 'citizen', label: 'US Citizen' },
  { value: 'permanent_resident', label: 'Permanent Resident' },
  { value: 'h1b', label: 'H-1B Visa' },
  { value: 'opt', label: 'OPT/CPT' },
  { value: 'ead', label: 'EAD' },
  { value: 'other', label: 'Other' },
];

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

const EMPTY_EDUCATION: EducationEntry = { school: '', degree: '', field: '', start_date: null, end_date: null };
const EMPTY_EXPERIENCE: ExperienceEntry = { company: '', title: '', start_date: null, end_date: null, description: null };

function initFormState(profile?: UserProfile): FormState {
  return {
    full_name: profile?.full_name ?? '',
    phone: profile?.phone ?? '',
    location: profile?.location ?? '',
    linkedin_url: profile?.linkedin_url ?? '',
    github_url: profile?.github_url ?? '',
    portfolio_url: profile?.portfolio_url ?? '',
    work_authorization: profile?.work_authorization ?? '',
    preferred_job_types: profile?.preferred_job_types ?? [],
    preferred_remote_types: profile?.preferred_remote_types ?? [],
    salary_min: profile?.salary_min?.toString() ?? '',
    salary_max: profile?.salary_max?.toString() ?? '',
    education: profile?.education ?? [],
    experience: profile?.work_experience ?? [],
    search_queries: profile?.search_queries ?? [],
    search_locations: profile?.search_locations ?? [],
    watchlist_companies: profile?.watchlist_companies ?? [],
    answer_bank: profile?.answer_bank ?? {},
  };
}

function CheckboxGroup({
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
  const toggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-text-secondary mb-2">{label}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => toggle(opt.value)}
            className={
              selected.includes(opt.value)
                ? 'px-3 py-1.5 text-sm font-medium rounded-[var(--radius-md)] border border-accent-primary bg-accent-primary/15 text-accent-primary transition-colors'
                : 'px-3 py-1.5 text-sm font-medium rounded-[var(--radius-md)] border border-border bg-bg-tertiary text-text-secondary hover:border-border-focus transition-colors'
            }
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function ListEditor({
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
  const [inputValue, setInputValue] = useState('');

  const handleAdd = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !items.includes(trimmed)) {
      onAdd(trimmed);
      setInputValue('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-text-secondary mb-1.5">{label}</label>
      <div className="flex gap-2 mb-2">
        <Input
          placeholder={placeholder}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <Button
          variant="secondary"
          onClick={handleAdd}
          disabled={!inputValue.trim()}
          icon={<Plus size={14} weight="bold" />}
        >
          Add
        </Button>
      </div>
      {items.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {items.map((item, index) => (
            <Badge key={`${item}-${index}`} variant="info" size="md">
              {item}
              <button
                type="button"
                onClick={() => onRemove(index)}
                className="ml-1.5 hover:text-accent-danger transition-colors"
              >
                <X size={12} weight="bold" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-bg-secondary border border-border rounded-[var(--radius-lg)] p-4 space-y-4">
            <Skeleton variant="text" className="w-1/3 h-5" />
            <Skeleton variant="rect" className="w-full h-10" />
            <Skeleton variant="rect" className="w-full h-10" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Profile() {
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: () => profileApi.get().then((r) => r.data),
  });

  const [form, setForm] = useState<FormState>(initFormState());

  useEffect(() => {
    if (profile) {
      setForm(initFormState(profile));
    }
  }, [profile]);

  const updateField = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const saveMutation = useMutation({
    mutationFn: (data: Partial<UserProfile>) => profileApi.update(data),
    onSuccess: () => {
      toast('success', 'Profile saved successfully');
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: () => {
      toast('error', 'Failed to save profile');
    },
  });

  const generateAnswersMutation = useMutation({
    mutationFn: () => profileApi.generateAnswers(),
    onSuccess: () => {
      toast('success', 'Answer bank generated from resume');
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: () => toast('error', 'Failed to generate answers'),
  });

  const handleSave = () => {
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
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-text-primary">Profile</h1>
        </div>
        <ProfileSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-xs font-medium text-text-muted tracking-tight">
            Account
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-text-primary">
            Profile
          </h1>
        </div>
        <Button
          variant="primary"
          onClick={handleSave}
          loading={saveMutation.isPending}
          icon={<FloppyDisk size={16} weight="bold" />}
        >
          Save Changes
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Personal Info */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <UserCircle size={16} weight="bold" className="text-accent-primary" />
            Personal Information
          </h2>
          <div className="space-y-4">
            <Input
              label="Full Name"
              placeholder="John Doe"
              value={form.full_name}
              onChange={(e) => updateField('full_name', e.target.value)}
              icon={<UserCircle size={16} weight="bold" />}
            />
            <Input
              label="Email"
              type="email"
              value={user?.email ?? ''}
              disabled
              icon={<Envelope size={16} weight="bold" />}
            />
            <Input
              label="Phone"
              type="tel"
              placeholder="+1 (555) 000-0000"
              value={form.phone}
              onChange={(e) => updateField('phone', e.target.value)}
              icon={<Phone size={16} weight="bold" />}
            />
            <Input
              label="Location"
              placeholder="San Francisco, CA"
              value={form.location}
              onChange={(e) => updateField('location', e.target.value)}
              icon={<MapPin size={16} weight="bold" />}
            />
          </div>
        </Card>

        {/* Links */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <LinkSimple size={16} weight="bold" className="text-accent-primary" />
            Links
          </h2>
          <div className="space-y-4">
            <Input
              label="LinkedIn"
              placeholder="https://linkedin.com/in/johndoe"
              value={form.linkedin_url}
              onChange={(e) => updateField('linkedin_url', e.target.value)}
              icon={<LinkSimple size={16} weight="bold" />}
            />
            <Input
              label="GitHub"
              placeholder="https://github.com/johndoe"
              value={form.github_url}
              onChange={(e) => updateField('github_url', e.target.value)}
              icon={<GithubLogo size={16} weight="bold" />}
            />
            <Input
              label="Portfolio"
              placeholder="https://johndoe.dev"
              value={form.portfolio_url}
              onChange={(e) => updateField('portfolio_url', e.target.value)}
              icon={<Globe size={16} weight="bold" />}
            />
            <Select
              label="Work Authorization"
              options={WORK_AUTH_OPTIONS}
              value={form.work_authorization}
              onChange={(e) => updateField('work_authorization', e.target.value)}
            />
          </div>
        </Card>

        {/* Preferences */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <Briefcase size={16} className="text-accent-primary" />
            Preferences
          </h2>
          <div className="space-y-5">
            <CheckboxGroup
              label="Preferred Job Types"
              options={JOB_TYPE_OPTIONS}
              selected={form.preferred_job_types}
              onChange={(values) => updateField('preferred_job_types', values)}
            />
            <CheckboxGroup
              label="Preferred Remote Types"
              options={REMOTE_TYPE_OPTIONS}
              selected={form.preferred_remote_types}
              onChange={(values) => updateField('preferred_remote_types', values)}
            />
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">Salary Range</label>
              <div className="flex items-center gap-3">
                <Input
                  type="number"
                  placeholder="Min"
                  value={form.salary_min}
                  onChange={(e) => updateField('salary_min', e.target.value)}
                  icon={<CurrencyDollar size={16} weight="bold" />}
                />
                <span className="text-text-muted text-sm">to</span>
                <Input
                  type="number"
                  placeholder="Max"
                  value={form.salary_max}
                  onChange={(e) => updateField('salary_max', e.target.value)}
                  icon={<CurrencyDollar size={16} weight="bold" />}
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Search Configuration */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <MagnifyingGlass size={16} weight="bold" className="text-accent-primary" />
            Search Configuration
          </h2>
          <div className="space-y-5">
            <ListEditor
              label="Search Queries"
              placeholder="e.g., Senior React Developer"
              items={form.search_queries}
              onAdd={(val) => updateField('search_queries', [...form.search_queries, val])}
              onRemove={(idx) =>
                updateField('search_queries', form.search_queries.filter((_, i) => i !== idx))
              }
            />
            <ListEditor
              label="Search Locations"
              placeholder="e.g., San Francisco, CA"
              items={form.search_locations}
              onAdd={(val) => updateField('search_locations', [...form.search_locations, val])}
              onRemove={(idx) =>
                updateField('search_locations', form.search_locations.filter((_, i) => i !== idx))
              }
            />
            <ListEditor
              label="Watchlist Companies"
              placeholder="e.g., Google"
              items={form.watchlist_companies}
              onAdd={(val) => updateField('watchlist_companies', [...form.watchlist_companies, val])}
              onRemove={(idx) =>
                updateField('watchlist_companies', form.watchlist_companies.filter((_, i) => i !== idx))
              }
            />
          </div>
        </Card>

        {/* Education */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <GraduationCap size={16} weight="bold" className="text-accent-primary" />
            Education
          </h2>
          <div className="space-y-3">
            {form.education.map((edu, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-bg-tertiary rounded-[var(--radius-md)]">
                <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <Input
                    placeholder="School"
                    value={edu.school}
                    onChange={(e) => {
                      const updated = [...form.education];
                      updated[idx] = { ...edu, school: e.target.value };
                      updateField('education', updated);
                    }}
                  />
                  <Input
                    placeholder="Degree (e.g., MS)"
                    value={edu.degree}
                    onChange={(e) => {
                      const updated = [...form.education];
                      updated[idx] = { ...edu, degree: e.target.value };
                      updateField('education', updated);
                    }}
                  />
                  <Input
                    placeholder="Field of Study"
                    value={edu.field}
                    onChange={(e) => {
                      const updated = [...form.education];
                      updated[idx] = { ...edu, field: e.target.value };
                      updateField('education', updated);
                    }}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => updateField('education', form.education.filter((_, i) => i !== idx))}
                  className="p-1.5 text-text-muted hover:text-accent-danger transition-colors"
                >
                  <X size={16} weight="bold" />
                </button>
              </div>
            ))}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => updateField('education', [...form.education, { ...EMPTY_EDUCATION }])}
              icon={<Plus size={14} weight="bold" />}
            >
              Add Education
            </Button>
          </div>
        </Card>

        {/* Work Experience */}
        <Card>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <Buildings size={16} weight="bold" className="text-accent-primary" />
            Work Experience
          </h2>
          <div className="space-y-3">
            {form.experience.map((exp, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-bg-tertiary rounded-[var(--radius-md)]">
                <div className="flex-1 space-y-2">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <Input
                      placeholder="Company"
                      value={exp.company}
                      onChange={(e) => {
                        const updated = [...form.experience];
                        updated[idx] = { ...exp, company: e.target.value };
                        updateField('experience', updated);
                      }}
                    />
                    <Input
                      placeholder="Title"
                      value={exp.title}
                      onChange={(e) => {
                        const updated = [...form.experience];
                        updated[idx] = { ...exp, title: e.target.value };
                        updateField('experience', updated);
                      }}
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <Input
                      placeholder="Start Date (YYYY-MM)"
                      value={exp.start_date ?? ''}
                      onChange={(e) => {
                        const updated = [...form.experience];
                        updated[idx] = { ...exp, start_date: e.target.value || null };
                        updateField('experience', updated);
                      }}
                    />
                    <Input
                      placeholder="End Date (YYYY-MM or Present)"
                      value={exp.end_date ?? ''}
                      onChange={(e) => {
                        const updated = [...form.experience];
                        updated[idx] = { ...exp, end_date: e.target.value || null };
                        updateField('experience', updated);
                      }}
                    />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => updateField('experience', form.experience.filter((_, i) => i !== idx))}
                  className="p-1.5 text-text-muted hover:text-accent-danger transition-colors"
                >
                  <X size={16} weight="bold" />
                </button>
              </div>
            ))}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => updateField('experience', [...form.experience, { ...EMPTY_EXPERIENCE }])}
              icon={<Plus size={14} weight="bold" />}
            >
              Add Experience
            </Button>
          </div>
        </Card>

        {/* Answer Bank */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <BookOpen size={16} weight="bold" className="text-accent-primary" />
              Answer Bank
            </h2>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => generateAnswersMutation.mutate()}
              loading={generateAnswersMutation.isPending}
              icon={<Sparkle size={14} weight="fill" />}
            >
              Generate from Resume
            </Button>
          </div>
          <div className="space-y-4">
            {Object.keys(form.answer_bank).length === 0 ? (
              <p className="text-sm text-text-muted">
                No answers yet. Click &ldquo;Generate from Resume&rdquo; to auto-fill common interview questions, or add entries manually.
              </p>
            ) : (
              Object.entries(form.answer_bank).map(([question, answer]) => (
                <div key={question} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-text-secondary">{question}</label>
                    <button
                      type="button"
                      onClick={() => {
                        const updated = { ...form.answer_bank };
                        delete updated[question];
                        updateField('answer_bank', updated);
                      }}
                      className="text-text-muted hover:text-accent-danger transition-colors"
                    >
                      <X size={14} weight="bold" />
                    </button>
                  </div>
                  <textarea
                    className="w-full bg-bg-tertiary border border-border rounded-[var(--radius-md)] px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-border-focus resize-y min-h-16"
                    value={answer}
                    onChange={(e) => updateField('answer_bank', { ...form.answer_bank, [question]: e.target.value })}
                    rows={2}
                  />
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
