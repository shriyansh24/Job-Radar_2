import {
  Clock,
  Brain,
  CaretDown,
  CaretRight,
  CheckCircle,
  ChatCircleText,
  Hash,
  ClockCounterClockwise,
  Sparkle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useState } from "react";
import { interviewApi, type InterviewQuestion, type InterviewSession } from "../api/interview";
import { jobsApi, type Job } from "../api/jobs";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/Toast";

const tabs = [
  { id: "practice", label: "Practice", icon: <Brain size={14} weight="bold" /> },
  {
    id: "history",
    label: "History",
    icon: <ClockCounterClockwise size={14} weight="bold" />,
  },
];

const QUESTION_TYPES = [
  { value: 'behavioral', label: 'Behavioral' },
  { value: 'technical', label: 'Technical' },
  { value: 'system_design', label: 'System Design' },
  { value: 'culture_fit', label: 'Culture Fit' },
] as const;

type QuestionType = (typeof QUESTION_TYPES)[number]['value'];

const COUNT_OPTIONS = Array.from({ length: 8 }, (_, i) => ({
  value: String(i + 3),
  label: String(i + 3),
}));

const CATEGORY_VARIANT: Record<string, 'info' | 'success' | 'warning' | 'danger' | 'default'> = {
  behavioral: 'info',
  technical: 'warning',
  system_design: 'danger',
  culture_fit: 'success',
};

const DIFFICULTY_VARIANT: Record<string, 'success' | 'warning' | 'danger' | 'default'> = {
  easy: 'success',
  medium: 'warning',
  hard: 'danger',
};

function GenerateForm({
  onGenerate,
  isPending,
}: {
  onGenerate: (params: { job_id: string; types: QuestionType[]; count: number }) => void;
  isPending: boolean;
}) {
  const [selectedJob, setSelectedJob] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<Set<QuestionType>>(new Set(['behavioral', 'technical']));
  const [count, setCount] = useState('5');

  const { data: jobs } = useQuery({
    queryKey: ['jobs', 'all'],
    queryFn: () => jobsApi.list({ page_size: 100 }).then((r) => r.data),
  });

  const jobOptions = (jobs?.items || []).map((j: Job) => ({
    value: j.id,
    label: `${j.title} - ${j.company_name || 'Unknown'}`,
  }));

  const toggleType = (type: QuestionType) => {
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        if (next.size > 1) next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const handleSubmit = () => {
    if (!selectedJob) {
      toast('warning', 'Please select a job first');
      return;
    }
    onGenerate({
      job_id: selectedJob,
      types: Array.from(selectedTypes),
      count: Number(count),
    });
  };

  return (
    <Card>
      <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2">
        <Sparkle size={16} weight="fill" className="text-accent-primary" />
        Generate Interview Questions
      </h2>
      <div className="space-y-4">
        <Select
          label="Target Job"
          options={jobOptions}
          value={selectedJob}
          onChange={(e) => setSelectedJob(e.target.value)}
          placeholder="Select a job..."
        />

        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1.5">
            Question Types
          </label>
          <div className="flex flex-wrap gap-2">
            {QUESTION_TYPES.map((qt) => (
              <button
                key={qt.value}
                type="button"
                onClick={() => toggleType(qt.value)}
                className={`px-3 py-1.5 text-sm rounded-[var(--radius-md)] border transition-colors duration-[var(--transition-fast)] ${
                  selectedTypes.has(qt.value)
                    ? 'bg-accent-primary/15 text-accent-primary border-accent-primary/30'
                    : 'bg-bg-tertiary text-text-muted border-border hover:border-border-focus'
                }`}
              >
                {qt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="w-32">
          <Select
            label="Question Count"
            options={COUNT_OPTIONS}
            value={count}
            onChange={(e) => setCount(e.target.value)}
          />
        </div>

        <Button
          variant="primary"
          loading={isPending}
          disabled={!selectedJob}
          onClick={handleSubmit}
          icon={<Sparkle size={14} weight="fill" />}
        >
          Generate Questions
        </Button>
      </div>
    </Card>
  );
}

function QuestionCard({
  question,
  index,
  sessionId,
}: {
  question: InterviewQuestion;
  index: number;
  sessionId: string;
}) {
  const [expanded, setExpanded] = useState(index === 0);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<{ score: number; feedback: string } | null>(null);

  const evaluateMutation = useMutation({
    mutationFn: () =>
      interviewApi.evaluate({ session_id: sessionId, question_index: index, answer }),
    onSuccess: (res) => {
      setFeedback(res.data);
      toast('success', 'Answer evaluated');
    },
    onError: () => toast('error', 'Evaluation failed'),
  });

  const categoryVariant = CATEGORY_VARIANT[question.category] || 'default';
  const difficultyVariant = DIFFICULTY_VARIANT[question.difficulty] || 'default';

  const scoreVariant =
    feedback && feedback.score >= 7
      ? 'success'
      : feedback && feedback.score >= 5
        ? 'warning'
        : 'danger';

  return (
    <Card>
      <button
        type="button"
        className="w-full text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-xs text-text-muted flex items-center gap-1 shrink-0">
              <Hash size={12} weight="bold" /> {index + 1}
            </span>
            <p className="text-sm font-medium text-text-primary truncate">
              {question.question}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Badge variant={categoryVariant} size="sm">
              {question.category.replace('_', ' ')}
            </Badge>
            <Badge variant={difficultyVariant} size="sm">
              {question.difficulty}
            </Badge>
            {feedback && (
              <Badge variant={scoreVariant} size="sm">
                {feedback.score}/10
              </Badge>
            )}
            {expanded ? (
              <CaretDown size={14} weight="bold" className="text-text-muted" />
            ) : (
              <CaretRight size={14} weight="bold" className="text-text-muted" />
            )}
          </div>
        </div>
      </button>

      {expanded && (
        <div className="mt-3 space-y-3 border-t border-border/50 pt-3">
          <p className="text-sm text-text-primary leading-relaxed">
            {question.question}
          </p>

          <Textarea
            placeholder="Type your answer here..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            className="min-h-[100px]"
          />

          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              size="sm"
              loading={evaluateMutation.isPending}
              disabled={!answer.trim()}
              onClick={() => evaluateMutation.mutate()}
              icon={<CheckCircle size={14} weight="bold" />}
            >
              Evaluate
            </Button>

            {feedback && (
              <Badge variant={scoreVariant} size="md">
                {feedback.score}/10
              </Badge>
            )}
          </div>

          {feedback && (
            <div className="mt-2 p-3 bg-bg-tertiary rounded-[var(--radius-md)] border border-border/50">
              <p className="text-xs font-medium text-text-secondary mb-1">Feedback</p>
              <p className="text-sm text-text-primary leading-relaxed">{feedback.feedback}</p>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function ActiveSession({ session }: { session: InterviewSession }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-semibold text-text-primary">Active Session</h2>
        <Badge variant="info" size="sm">
          {session.questions.length} questions
        </Badge>
      </div>
      {session.questions.map((q, i) => (
        <QuestionCard key={i} question={q} index={i} sessionId={session.id} />
      ))}
    </div>
  );
}

function getSessionScore(session: InterviewSession): number | null {
  if (session.overall_score !== null) return session.overall_score;
  const scored = (session.scores || []).filter((s) => s.score != null);
  if (scored.length === 0) return null;
  return scored.reduce((sum, s) => sum + (Number(s.score) || 0), 0) / scored.length;
}

function SessionHistoryCard({
  session,
  onSelect,
}: {
  session: InterviewSession;
  onSelect: () => void;
}) {
  const overallScore = getSessionScore(session);
  const scoreVariant = overallScore !== null
    ? overallScore >= 7 ? 'success' : overallScore >= 5 ? 'warning' : 'danger'
    : 'default';

  return (
    <Card hover onClick={onSelect}>
      <div className="flex items-center justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <ChatCircleText size={14} weight="bold" className="text-accent-primary shrink-0" />
            <p className="text-sm font-medium text-text-primary truncate">
              Session {session.id.slice(0, 8)}
            </p>
            {overallScore !== null && (
              <Badge variant={scoreVariant} size="sm">
                Score: {overallScore.toFixed(1)}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-text-muted">
            <span className="flex items-center gap-1">
              <Clock size={10} weight="bold" />
              {format(new Date(session.created_at), 'PP')}
            </span>
            <span>{session.questions.length} questions</span>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {Array.from(new Set(session.questions.map((q) => q.category))).map((cat) => (
              <Badge key={cat} variant={CATEGORY_VARIANT[cat] || 'default'} size="sm">
                {cat.replace('_', ' ')}
              </Badge>
            ))}
          </div>
        </div>
        <CaretRight size={16} weight="bold" className="text-text-muted shrink-0" />
      </div>
    </Card>
  );
}

export default function InterviewPrep() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('practice');
  const [activeSession, setActiveSession] = useState<InterviewSession | null>(null);

  const { data: sessions, isLoading: loadingSessions } = useQuery({
    queryKey: ['interview-sessions'],
    queryFn: () => interviewApi.listSessions().then((r) => r.data),
  });

  const generateMutation = useMutation({
    mutationFn: (params: { job_id: string; types: QuestionType[]; count: number }) =>
      interviewApi.generate(params),
    onSuccess: (res) => {
      setActiveSession(res.data);
      toast('success', 'Interview questions generated');
      queryClient.invalidateQueries({ queryKey: ['interview-sessions'] });
    },
    onError: () => toast('error', 'Failed to generate questions'),
  });

  const loadSessionMutation = useMutation({
    mutationFn: (id: string) => interviewApi.getSession(id),
    onSuccess: (res) => {
      setActiveSession(res.data);
      setActiveTab('practice');
    },
    onError: () => toast('error', 'Failed to load session'),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text-primary">Interview Prep</h1>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'practice' && (
        <div className="space-y-6">
          <GenerateForm
            onGenerate={(params) => generateMutation.mutate(params)}
            isPending={generateMutation.isPending}
          />

          {activeSession && <ActiveSession session={activeSession} />}

          {!activeSession && !generateMutation.isPending && (
            <EmptyState
              icon={<Brain size={40} weight="bold" />}
              title="No active session"
              description="Select a job and generate questions to start practicing"
            />
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-4">
          {loadingSessions ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="bg-bg-secondary border border-border rounded-[var(--radius-lg)] p-4 space-y-3">
                  <Skeleton variant="text" className="w-1/3 h-4" />
                  <Skeleton variant="text" className="w-1/2 h-3" />
                  <div className="flex gap-2">
                    <Skeleton variant="rect" className="w-20 h-5" />
                    <Skeleton variant="rect" className="w-20 h-5" />
                  </div>
                </div>
              ))}
            </div>
          ) : !sessions || sessions.length === 0 ? (
            <EmptyState
              icon={<ClockCounterClockwise size={40} weight="bold" />}
              title="No sessions yet"
              description="Generate your first set of interview questions to get started"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sessions.map((session: InterviewSession) => (
                <SessionHistoryCard
                  key={session.id}
                  session={session}
                  onSelect={() => loadSessionMutation.mutate(session.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
