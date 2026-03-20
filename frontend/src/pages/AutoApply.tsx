import {
  ChartBar,
  CheckCircle,
  Clock,
  Envelope,
  Lightning,
  Plus,
  Pulse,
  X,
  XCircle,
  User,
  Shield,
  ShieldCheck,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useState } from "react";
import {
  autoApplyApi,
  type AutoApplyProfile,
  type AutoApplyRule,
  type AutoApplyRun,
  type AutoApplyProfileCreate,
  type AutoApplyRuleCreate,
} from "../api/auto-apply";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import { SkeletonCard } from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/Toast";

const TABS = [
  { id: "profiles", label: "Profiles", icon: <User size={14} weight="bold" /> },
  { id: "rules", label: "Rules", icon: <Shield size={14} weight="bold" /> },
  { id: "history", label: "Run History", icon: <Clock size={14} weight="bold" /> },
  { id: "stats", label: "Statistics", icon: <ChartBar size={14} weight="bold" /> },
];

const EMPTY_PROFILE: AutoApplyProfileCreate = {
  name: '',
  email: '',
  phone: '',
  linkedin_url: '',
  github_url: '',
  portfolio_url: '',
  cover_letter_template: '',
};

const EMPTY_RULE: AutoApplyRuleCreate = {
  name: '',
  min_match_score: undefined,
  required_keywords: [],
  excluded_keywords: [],
};

function ProfileCard({
  profile,
}: {
  profile: AutoApplyProfile;
}) {
  return (
    <Card hover>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-text-primary truncate">{profile.name}</p>
            {profile.is_active && (
              <Badge variant="success" size="sm">Active</Badge>
            )}
          </div>
          <p className="text-xs text-text-muted flex items-center gap-1 mt-1">
            <Envelope size={12} weight="bold" />
            {profile.email}
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-border">
        {profile.phone && (
          <Badge size="sm">Phone</Badge>
        )}
        {profile.linkedin_url && (
          <Badge variant="info" size="sm">LinkedIn</Badge>
        )}
        {profile.github_url && (
          <Badge variant="info" size="sm">GitHub</Badge>
        )}
        {profile.portfolio_url && (
          <Badge variant="info" size="sm">Portfolio</Badge>
        )}
        {profile.cover_letter_template && (
          <Badge variant="default" size="sm">Template</Badge>
        )}
      </div>
    </Card>
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
    <Card hover>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-text-primary truncate">{rule.name}</p>
            <Badge
              variant={rule.is_active ? 'success' : 'default'}
              size="sm"
            >
              {rule.is_active ? 'Active' : 'Inactive'}
            </Badge>
          </div>
          {rule.min_match_score !== null && (
            <p className="text-xs text-text-muted mt-1">
              Min match score: {rule.min_match_score}%
            </p>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleActive}
          icon={
            rule.is_active ? (
              <ShieldCheck size={14} weight="bold" />
            ) : (
              <Shield size={14} weight="bold" />
            )
          }
        >
          {rule.is_active ? 'Deactivate' : 'Activate'}
        </Button>
      </div>
      {(rule.required_keywords.length > 0 || rule.excluded_keywords.length > 0) && (
        <div className="mt-3 pt-3 border-t border-border space-y-2">
          {rule.required_keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs text-text-muted mr-1">Required:</span>
              {rule.required_keywords.map((kw) => (
                <Badge key={kw} variant="success" size="sm">{kw}</Badge>
              ))}
            </div>
          )}
          {rule.excluded_keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs text-text-muted mr-1">Excluded:</span>
              {rule.excluded_keywords.map((kw) => (
                <Badge key={kw} variant="danger" size="sm">{kw}</Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function StatCard({
  icon,
  label,
  value,
  variant,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  variant: 'default' | 'success' | 'danger' | 'warning';
}) {
  const variantClasses = {
    default: 'text-text-primary',
    success: 'text-accent-success',
    danger: 'text-accent-danger',
    warning: 'text-accent-warning',
  };

  return (
    <Card>
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-[var(--radius-md)] bg-bg-tertiary">
          {icon}
        </div>
        <div>
          <p className={`text-2xl font-bold ${variantClasses[variant]}`}>{value}</p>
          <p className="text-xs text-text-muted">{label}</p>
        </div>
      </div>
    </Card>
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
      toast('success', 'Profile created');
      queryClient.invalidateQueries({ queryKey: ['auto-apply-profiles'] });
      onClose();
      setForm({ ...EMPTY_PROFILE });
    },
    onError: () => toast('error', 'Failed to create profile'),
  });

  return (
    <Modal open={open} onClose={onClose} title="Add Profile" size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="e.g. Default Profile"
          />
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            placeholder="e.g. john@example.com"
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Phone"
            value={form.phone ?? ''}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            placeholder="e.g. +1 555 123 4567"
          />
          <Input
            label="LinkedIn URL"
            value={form.linkedin_url ?? ''}
            onChange={(e) => setForm({ ...form, linkedin_url: e.target.value })}
            placeholder="e.g. https://linkedin.com/in/johndoe"
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="GitHub URL"
            value={form.github_url ?? ''}
            onChange={(e) => setForm({ ...form, github_url: e.target.value })}
            placeholder="e.g. https://github.com/johndoe"
          />
          <Input
            label="Portfolio URL"
            value={form.portfolio_url ?? ''}
            onChange={(e) => setForm({ ...form, portfolio_url: e.target.value })}
            placeholder="e.g. https://johndoe.dev"
          />
        </div>
        <Textarea
          label="Cover Letter Template"
          value={form.cover_letter_template ?? ''}
          onChange={(e) => setForm({ ...form, cover_letter_template: e.target.value })}
          placeholder="Write a default cover letter template. Use {company} and {position} as placeholders..."
          rows={5}
        />
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
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
  const [inputValue, setInputValue] = useState('');

  const addKeyword = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !keywords.includes(trimmed)) {
      onChange([...keywords, trimmed]);
      setInputValue('');
    }
  };

  const removeKeyword = (keyword: string) => {
    onChange(keywords.filter((kw) => kw !== keyword));
  };

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-text-secondary mb-1.5">
        {label}
      </label>
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={placeholder}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              addKeyword();
            }
          }}
        />
        <Button variant="secondary" size="md" onClick={addKeyword} disabled={!inputValue.trim()}>
          Add
        </Button>
      </div>
      {keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {keywords.map((kw) => (
            <Badge key={kw} size="sm">
              <span className="flex items-center gap-1">
                {kw}
                <button
                  type="button"
                  onClick={() => removeKeyword(kw)}
                  className="text-text-muted hover:text-text-primary ml-0.5"
                >
                  <X size={10} weight="bold" />
                </button>
              </span>
            </Badge>
          ))}
        </div>
      )}
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
      toast('success', 'Rule created');
      queryClient.invalidateQueries({ queryKey: ['auto-apply-rules'] });
      onClose();
      setForm({ ...EMPTY_RULE });
    },
    onError: () => toast('error', 'Failed to create rule'),
  });

  return (
    <Modal open={open} onClose={onClose} title="Add Rule" size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Rule Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="e.g. Senior Frontend Roles"
          />
          <Input
            label="Min Match Score (%)"
            type="number"
            min={0}
            max={100}
            value={form.min_match_score ?? ''}
            onChange={(e) =>
              setForm({
                ...form,
                min_match_score: e.target.value ? Number(e.target.value) : undefined,
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
        <div className="flex items-center gap-2 pt-1">
          <input
            type="checkbox"
            id="rule-active"
            className="rounded border-border text-accent-primary focus:ring-accent-primary"
            defaultChecked
          />
          <label htmlFor="rule-active" className="text-sm text-text-secondary">
            Enable rule immediately
          </label>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
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
  const [activeTab, setActiveTab] = useState('profiles');
  const [showCreateProfile, setShowCreateProfile] = useState(false);
  const [showCreateRule, setShowCreateRule] = useState(false);

  // Queries
  const { data: profiles, isLoading: profilesLoading } = useQuery({
    queryKey: ['auto-apply-profiles'],
    queryFn: () => autoApplyApi.listProfiles().then((r) => r.data),
  });

  const { data: rules, isLoading: rulesLoading } = useQuery({
    queryKey: ['auto-apply-rules'],
    queryFn: () => autoApplyApi.listRules().then((r) => r.data),
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['auto-apply-stats'],
    queryFn: () => autoApplyApi.getStats().then((r) => r.data),
  });

  const toggleRuleMutation = useMutation({
    mutationFn: (rule: AutoApplyRule) =>
      autoApplyApi.updateRule(rule.id, { name: rule.name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auto-apply-rules'] });
      toast('success', 'Rule updated');
    },
    onError: () => toast('error', 'Failed to update rule'),
  });

  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ['auto-apply-runs'],
    queryFn: () => autoApplyApi.runs().then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text-primary">Auto Apply</h1>

      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {/* Profiles Tab */}
      {activeTab === 'profiles' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button
              variant="primary"
              onClick={() => setShowCreateProfile(true)}
              icon={<Plus size={14} weight="bold" />}
            >
              Add Profile
            </Button>
          </div>

          {profilesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 2 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : !profiles || profiles.length === 0 ? (
            <EmptyState
              icon={<User size={40} weight="bold" />}
              title="No profiles yet"
              description="Create your first auto-apply profile with your contact details and cover letter template"
              action={{ label: 'Add Profile', onClick: () => setShowCreateProfile(true) }}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {profiles.map((profile: AutoApplyProfile) => (
                <ProfileCard key={profile.id} profile={profile} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button
              variant="primary"
              onClick={() => setShowCreateRule(true)}
              icon={<Plus size={14} weight="bold" />}
            >
              Add Rule
            </Button>
          </div>

          {rulesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 2 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : !rules || rules.length === 0 ? (
            <EmptyState
              icon={<Shield size={40} weight="bold" />}
              title="No rules yet"
              description="Set up rules to automatically apply to jobs that match your criteria"
              action={{ label: 'Add Rule', onClick: () => setShowCreateRule(true) }}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {rules.map((rule: AutoApplyRule) => (
                <RuleCard
                  key={rule.id}
                  rule={rule}
                  onToggleActive={() => toggleRuleMutation.mutate(rule)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Run History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {runsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : !runs || runs.length === 0 ? (
            <EmptyState
              icon={<Clock size={40} weight="bold" />}
              title="No run history"
              description="Run history will appear here after auto-apply processes jobs"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-text-muted font-medium">Job</th>
                    <th className="text-left py-3 px-4 text-text-muted font-medium">Status</th>
                    <th className="text-left py-3 px-4 text-text-muted font-medium">ATS</th>
                    <th className="text-left py-3 px-4 text-text-muted font-medium">Fields Filled</th>
                    <th className="text-left py-3 px-4 text-text-muted font-medium">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run: AutoApplyRun) => {
                    const statusVariant: Record<string, 'success' | 'danger' | 'warning' | 'info' | 'default'> = {
                      completed: 'success',
                      failed: 'danger',
                      pending: 'warning',
                      running: 'info',
                    };
                    return (
                      <tr key={run.id} className="border-b border-border/50 hover:bg-bg-tertiary/50">
                        <td className="py-3 px-4 text-text-primary">{run.job_id.slice(0, 8)}...</td>
                        <td className="py-3 px-4">
                          <Badge variant={statusVariant[run.status] || 'default'} size="sm">
                            {run.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-text-secondary">{run.ats_provider || '—'}</td>
                        <td className="py-3 px-4 text-text-secondary">
                          {Object.keys(run.fields_filled).length} filled
                          {run.fields_missed.length > 0 && (
                            <span className="text-accent-danger ml-1">({run.fields_missed.length} missed)</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-text-muted">
                          {run.completed_at
                            ? format(new Date(run.completed_at), 'PP p')
                            : run.started_at
                              ? format(new Date(run.started_at), 'PP p')
                              : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Stats Tab */}
      {activeTab === 'stats' && (
        <div className="space-y-6">
          {statsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : stats ? (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  icon={<Pulse size={20} weight="bold" className="text-text-primary" />}
                  label="Total Runs"
                  value={stats.total_runs}
                  variant="default"
                />
                <StatCard
                  icon={<CheckCircle size={20} weight="bold" className="text-accent-success" />}
                  label="Successful"
                  value={stats.successful}
                  variant="success"
                />
                <StatCard
                  icon={<XCircle size={20} weight="bold" className="text-accent-danger" />}
                  label="Failed"
                  value={stats.failed}
                  variant="danger"
                />
                <StatCard
                  icon={<Clock size={20} weight="bold" className="text-accent-warning" />}
                  label="Pending"
                  value={stats.pending}
                  variant="warning"
                />
              </div>

              <Card>
                <div className="flex items-center gap-3 mb-3">
                  <Lightning size={18} weight="bold" className="text-accent-primary" />
                  <h3 className="text-sm font-medium text-text-primary">Summary</h3>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-text-secondary">
                    Auto-apply has processed <span className="font-medium text-text-primary">{stats.total_runs}</span> total
                    runs with a success rate of{' '}
                    <span className="font-medium text-accent-success">
                      {stats.total_runs > 0
                        ? ((stats.successful / stats.total_runs) * 100).toFixed(1)
                        : '0.0'}
                      %
                    </span>
                    .
                  </p>
                  {stats.pending > 0 && (
                    <p className="text-sm text-text-muted">
                      There {stats.pending === 1 ? 'is' : 'are'}{' '}
                      <span className="font-medium text-accent-warning">{stats.pending}</span>{' '}
                      pending {stats.pending === 1 ? 'application' : 'applications'} in the queue.
                    </p>
                  )}
                  {stats.failed > 0 && (
                    <p className="text-sm text-text-muted">
                      <span className="font-medium text-accent-danger">{stats.failed}</span>{' '}
                      {stats.failed === 1 ? 'run has' : 'runs have'} failed. Review your rules and
                      profiles to improve success rate.
                    </p>
                  )}
                </div>
              </Card>
            </>
          ) : (
            <EmptyState
              icon={<ChartBar size={40} weight="bold" />}
              title="No stats available"
              description="Stats will appear here once auto-apply starts processing jobs"
            />
          )}
        </div>
      )}

      {/* Modals */}
      <CreateProfileModal
        open={showCreateProfile}
        onClose={() => setShowCreateProfile(false)}
      />
      <CreateRuleModal
        open={showCreateRule}
        onClose={() => setShowCreateRule(false)}
      />
    </div>
  );
}
