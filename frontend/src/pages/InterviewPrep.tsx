import {
  Brain,
  CaretDown,
  CaretRight,
  ChatCircleText,
  CheckCircle,
  Clock,
  ClockCounterClockwise,
  Hash,
  Sparkle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import { useMemo, useState } from "react";
import { interviewApi, type InterviewQuestion, type InterviewSession } from "../api/interview";
import { jobsApi, type Job } from "../api/jobs";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/toastService";

const tabs = [
  { id: "practice", label: "Practice", icon: <Brain size={14} weight="bold" /> },
  { id: "history", label: "History", icon: <ClockCounterClockwise size={14} weight="bold" /> },
] as const;

const QUESTION_TYPES = [
  { value: "behavioral", label: "Behavioral" },
  { value: "technical", label: "Technical" },
  { value: "system_design", label: "System Design" },
  { value: "culture_fit", label: "Culture Fit" },
] as const;

type QuestionType = (typeof QUESTION_TYPES)[number]["value"];

const COUNT_OPTIONS = Array.from({ length: 8 }, (_, index) => ({
  value: String(index + 3),
  label: String(index + 3),
}));

const CATEGORY_VARIANT: Record<string, "info" | "success" | "warning" | "danger" | "default"> = {
  behavioral: "info",
  technical: "warning",
  system_design: "danger",
  culture_fit: "success",
};

const DIFFICULTY_VARIANT: Record<string, "success" | "warning" | "danger" | "default"> = {
  easy: "success",
  medium: "warning",
  hard: "danger",
};

function getQuestionCategory(question: InterviewQuestion): string {
  return question.category || question.type || "behavioral";
}

function getQuestionDifficulty(question: InterviewQuestion): string {
  return question.difficulty || "medium";
}

function getSessionScore(session: InterviewSession): number | null {
  if (session.overall_score !== null) return session.overall_score;
  const scored = (session.scores || []).filter((score) => score.score != null);
  if (scored.length === 0) return null;
  return scored.reduce((sum, score) => sum + (Number(score.score) || 0), 0) / scored.length;
}

function GenerateForm({
  onGenerate,
  isPending,
}: {
  onGenerate: (params: { job_id: string; types: QuestionType[]; count: number }) => void;
  isPending: boolean;
}) {
  const [selectedJob, setSelectedJob] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<Set<QuestionType>>(
    new Set(["behavioral", "technical"])
  );
  const [count, setCount] = useState("5");

  const { data: jobs } = useQuery({
    queryKey: ["jobs", "all"],
    queryFn: () => jobsApi.list({ page_size: 100 }).then((response) => response.data),
  });

  const jobOptions = (jobs?.items || []).map((job: Job) => ({
    value: job.id,
    label: `${job.title} - ${job.company_name || "Unknown"}`,
  }));

  const toggleType = (type: QuestionType) => {
    setSelectedTypes((current) => {
      const next = new Set(current);
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
      toast("warning", "Please select a job first");
      return;
    }

    onGenerate({
      job_id: selectedJob,
      types: Array.from(selectedTypes),
      count: Number(count),
    });
  };

  return (
    <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
      <SectionHeader
        title="Generate Interview Questions"
        description="Ground the session in a real job target, pick the question mix, and then start practicing in-place."
      />
      <div className="mt-5 space-y-4">
        <Select
          label="Target Job"
          options={jobOptions}
          value={selectedJob}
          onChange={(event) => setSelectedJob(event.target.value)}
          placeholder="Select a job..."
        />

        <div>
          <label className="block font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
            Question Types
          </label>
          <div className="mt-2 flex flex-wrap gap-2">
            {QUESTION_TYPES.map((questionType) => (
              <button
                key={questionType.value}
                type="button"
                onClick={() => toggleType(questionType.value)}
                className={
                  selectedTypes.has(questionType.value)
                    ? "border-2 border-foreground bg-foreground px-3 py-2 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-background shadow-[var(--shadow-xs)]"
                    : "brutal-panel px-3 py-2 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-text-secondary"
                }
              >
                {questionType.label}
              </button>
            ))}
          </div>
        </div>

        <div className="max-w-32">
          <Select
            label="Question Count"
            options={COUNT_OPTIONS}
            value={count}
            onChange={(event) => setCount(event.target.value)}
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
    </Surface>
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
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<{ score: number; feedback: string } | null>(null);

  const evaluateMutation = useMutation({
    mutationFn: () =>
      interviewApi.evaluate({ session_id: sessionId, question_index: index, answer }),
    onSuccess: (response) => {
      setFeedback(response.data);
      toast("success", "Answer evaluated");
    },
    onError: () => toast("error", "Evaluation failed"),
  });

  const category = getQuestionCategory(question);
  const difficulty = getQuestionDifficulty(question);
  const categoryVariant = CATEGORY_VARIANT[category] || "default";
  const difficultyVariant = DIFFICULTY_VARIANT[difficulty] || "default";
  const scoreVariant =
    feedback && feedback.score >= 7 ? "success" : feedback && feedback.score >= 5 ? "warning" : "danger";

  return (
    <Surface tone="default" padding="lg" radius="xl" className="brutal-panel">
      <button type="button" className="w-full text-left" onClick={() => setExpanded((current) => !current)}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                <Hash size={12} weight="bold" className="inline-block" /> {index + 1}
              </span>
            </div>
            <p className="mt-2 text-sm font-semibold leading-6 text-text-primary">{question.question}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={categoryVariant}>{category.replace("_", " ")}</Badge>
            <Badge variant={difficultyVariant}>{difficulty}</Badge>
            {feedback ? <Badge variant={scoreVariant}>{feedback.score}/10</Badge> : null}
            {expanded ? <CaretDown size={16} weight="bold" /> : <CaretRight size={16} weight="bold" />}
          </div>
        </div>
      </button>

      {expanded ? (
        <div className="mt-4 border-t-2 border-border pt-4">
          <Textarea
            placeholder="Type your answer here..."
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            className="min-h-[120px]"
          />
          <div className="mt-4 flex items-center gap-3">
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
            {feedback ? <Badge variant={scoreVariant}>{feedback.score}/10</Badge> : null}
          </div>

          {feedback ? (
            <div className="brutal-panel mt-4 p-4">
              <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                Feedback
              </div>
              <p className="mt-2 text-sm leading-6 text-text-secondary">{feedback.feedback}</p>
            </div>
          ) : null}
        </div>
      ) : null}
    </Surface>
  );
}

function SessionHistoryCard({
  session,
  onSelect,
}: {
  session: InterviewSession;
  onSelect: () => void;
}) {
  const overallScore = getSessionScore(session);
  const scoreVariant =
    overallScore !== null ? (overallScore >= 7 ? "success" : overallScore >= 5 ? "warning" : "danger") : "default";

  return (
    <Surface tone="default" padding="lg" radius="xl" interactive onClick={onSelect} className="brutal-panel">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <ChatCircleText size={16} weight="bold" className="text-accent-primary" />
            <p className="truncate text-sm font-semibold text-text-primary">Session {session.id.slice(0, 8)}</p>
            {overallScore !== null ? <Badge variant={scoreVariant}>Score: {overallScore.toFixed(1)}</Badge> : null}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-text-muted">
            <span className="flex items-center gap-1">
              <Clock size={12} weight="bold" />
              {format(new Date(session.created_at), "PP")}
            </span>
            <span>{session.questions.length} questions</span>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {Array.from(new Set(session.questions.map(getQuestionCategory))).map((category) => (
              <Badge key={category} variant={CATEGORY_VARIANT[category] || "default"}>
                {category.replace("_", " ")}
              </Badge>
            ))}
          </div>
        </div>
        <CaretRight size={16} weight="bold" className="text-text-muted" />
      </div>
    </Surface>
  );
}

export default function InterviewPrep() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("practice");
  const [activeSession, setActiveSession] = useState<InterviewSession | null>(null);

  const { data: sessions, isLoading: loadingSessions } = useQuery({
    queryKey: ["interview-sessions"],
    queryFn: () => interviewApi.listSessions().then((response) => response.data),
  });

  const generateMutation = useMutation({
    mutationFn: (params: { job_id: string; types: QuestionType[]; count: number }) =>
      interviewApi.generate(params),
    onSuccess: (response) => {
      setActiveSession(response.data);
      toast("success", "Interview questions generated");
      queryClient.invalidateQueries({ queryKey: ["interview-sessions"] });
    },
    onError: () => toast("error", "Failed to generate questions"),
  });

  const loadSessionMutation = useMutation({
    mutationFn: (id: string) => interviewApi.getSession(id),
    onSuccess: (response) => {
      setActiveSession(response.data);
      setActiveTab("practice");
    },
    onError: () => toast("error", "Failed to load session"),
  });

  const metrics = useMemo(
    () => [
      {
        key: "sessions",
        label: "Sessions",
        value: `${sessions?.length ?? 0}`,
        hint: "Generated practice sessions available in the workspace.",
        icon: <ClockCounterClockwise size={18} weight="bold" />,
      },
      {
        key: "active",
        label: "Active session",
        value: activeSession ? `${activeSession.questions.length}` : "0",
        hint: activeSession ? "Questions currently loaded into practice mode." : "No active session loaded.",
        icon: <Brain size={18} weight="bold" />,
        tone: activeSession ? ("success" as const) : ("default" as const),
      },
      {
        key: "latest",
        label: "Latest score",
        value:
          sessions?.[0] && getSessionScore(sessions[0]) !== null
            ? `${getSessionScore(sessions[0])?.toFixed(1)}`
            : "-",
        hint: "Overall score from the most recent practice session.",
        icon: <CheckCircle size={18} weight="bold" />,
      },
      {
        key: "mode",
        label: "Mode",
        value: activeTab === "practice" ? "Practice" : "History",
        hint: "Whether you are generating questions or scanning prior sessions.",
        icon: <Sparkle size={18} weight="bold" />,
      },
    ],
    [activeSession, activeTab, sessions]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        className="hero-panel"
        eyebrow="Prepare"
        title="Interview Prep"
        description="Generate questions from a target job, practice answers, and keep the full session history close by."
      />

      <MetricStrip items={metrics} />

      <Tabs tabs={tabs.map((tab) => ({ ...tab }))} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "practice" ? (
        <SplitWorkspace
          primary={
            <div className="space-y-6">
              <GenerateForm
                onGenerate={(params) => generateMutation.mutate(params)}
                isPending={generateMutation.isPending}
              />

              {activeSession ? (
                <div className="space-y-4">
                  <SectionHeader
                    title="Active Session"
                    description={`${activeSession.questions.length} questions loaded for this practice round.`}
                  />
                  {activeSession.questions.map((question, index) => (
                    <QuestionCard
                      key={`${activeSession.id}-${index}`}
                      question={question}
                      index={index}
                      sessionId={activeSession.id}
                    />
                  ))}
                </div>
              ) : null}

              {!activeSession && !generateMutation.isPending ? (
                <Surface tone="default" padding="lg" radius="xl">
                  <EmptyState
                    icon={<Brain size={40} weight="bold" />}
                    title="No active session"
                    description="Select a job and generate questions to start practicing"
                  />
                </Surface>
              ) : null}
            </div>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="neutral"
                icon={<Sparkle size={18} weight="bold" />}
                title="Practice flow"
                description="Generate a set, answer in-line, then use evaluation scores to find weak spots before the next loop."
              />
              <StateBlock
                tone="warning"
                icon={<ClockCounterClockwise size={18} weight="bold" />}
                title="History handoff"
                description="Load a prior session from History whenever you want to revisit a category mix or compare scores over time."
              />
            </div>
          }
        />
      ) : null}

      {activeTab === "history" ? (
        <div className="space-y-4">
          {loadingSessions ? (
            <div className="grid gap-4 md:grid-cols-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <Surface key={index} tone="default" padding="lg" radius="xl" className="brutal-panel">
                  <Skeleton variant="text" className="h-4 w-1/3" />
                  <Skeleton variant="text" className="mt-3 h-4 w-1/2" />
                  <div className="mt-3 flex gap-2">
                    <Skeleton variant="rect" className="h-6 w-20" />
                    <Skeleton variant="rect" className="h-6 w-20" />
                  </div>
                </Surface>
              ))}
            </div>
          ) : !sessions || sessions.length === 0 ? (
            <Surface tone="default" padding="lg" radius="xl" className="brutal-panel">
              <EmptyState
                icon={<ClockCounterClockwise size={40} weight="bold" />}
                title="No sessions yet"
                description="Generate your first set of interview questions to get started"
              />
            </Surface>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
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
      ) : null}
    </div>
  );
}
