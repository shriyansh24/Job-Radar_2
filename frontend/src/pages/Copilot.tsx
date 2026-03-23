import {
  ArrowsOutCardinal,
  Brain,
  Briefcase,
  ClockCounterClockwise,
  FileText,
  Lightbulb,
  MagicWand,
  Sparkle,
} from "@phosphor-icons/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { startTransition, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { copilotApi, type CoverLetterResult } from "../api/copilot";
import { jobsApi } from "../api/jobs";
import Badge from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import Textarea from "../components/ui/Textarea";
import { toast } from "../components/ui/toastService";
import { cn } from "../lib/utils";

type CopilotTab = "assistant" | "history" | "letters";

interface TranscriptEntry {
  id: string;
  role: "user" | "assistant";
  content: string;
  label: string;
}

const COPILOT_TABS = [
  { id: "assistant", label: "Assistant", icon: <Sparkle size={14} weight="bold" /> },
  { id: "history", label: "Ask History", icon: <ClockCounterClockwise size={14} weight="bold" /> },
  { id: "letters", label: "Cover Letters", icon: <FileText size={14} weight="bold" /> },
] as const;

const CHAT_PROMPTS = [
  "Summarize the strongest targets in my current search.",
  "Turn my recent applications into a focused follow-up plan.",
  "Find the gaps between my profile and senior frontend roles.",
];

const HISTORY_PROMPTS = [
  "Which companies tend to ghost me after screening?",
  "What interview patterns show up in my outcomes?",
  "Which roles are converting better than average for me?",
];

const LETTER_STYLES = [
  { value: "professional", label: "Professional" },
  { value: "startup", label: "Startup" },
  { value: "technical", label: "Technical" },
  { value: "career-change", label: "Career Change" },
];

function MetricCard({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: React.ReactNode;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-text-muted">
            {label}
          </div>
          <div className="mt-2 text-2xl font-semibold tracking-tight text-text-primary">
            {value}
          </div>
          <p className="mt-2 text-sm text-text-secondary">{hint}</p>
        </div>
        <div className="rounded-[var(--radius-lg)] border border-border bg-bg-tertiary p-2 text-text-muted">
          {icon}
        </div>
      </div>
    </Card>
  );
}

export default function Copilot() {
  const [activeTab, setActiveTab] = useState<CopilotTab>("assistant");
  const [selectedJobId, setSelectedJobId] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [historyQuestion, setHistoryQuestion] = useState("");
  const [historyAnswer, setHistoryAnswer] = useState("");
  const [coverLetterStyle, setCoverLetterStyle] = useState("professional");
  const [coverLetterTemplate, setCoverLetterTemplate] = useState("");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [coverLetter, setCoverLetter] = useState<CoverLetterResult | null>(null);

  const { data: recentJobs, isLoading: loadingJobs } = useQuery({
    queryKey: ["jobs", "copilot-context"],
    queryFn: () =>
      jobsApi
        .list({ page_size: 10, sort_by: "scraped_at", sort_order: "desc" })
        .then((response) => response.data),
  });

  useEffect(() => {
    if (!selectedJobId && recentJobs?.items.length) {
      setSelectedJobId(recentJobs.items[0].id);
    }
  }, [recentJobs, selectedJobId]);

  const jobOptions =
    recentJobs?.items.map((job) => ({
      value: job.id,
      label: `${job.title} • ${job.company_name ?? "Unknown company"}`,
    })) ?? [];

  const selectedJob = recentJobs?.items.find((job) => job.id === selectedJobId) ?? null;

  const chatMutation = useMutation({
    mutationFn: async (message: string) =>
      copilotApi
        .chat(
          message,
          selectedJob
            ? {
                job_title: selectedJob.title,
                company_name: selectedJob.company_name,
                location: selectedJob.location,
                match_score: selectedJob.match_score,
              }
            : null,
          selectedJobId || undefined
        )
        .then((response) => response.data),
    onSuccess: (response) => {
      setTranscript((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.response,
          label: "Career Copilot",
        },
      ]);
      setChatInput("");
    },
    onError: () => toast("error", "Copilot could not respond right now"),
  });

  const askHistoryMutation = useMutation({
    mutationFn: (question: string) => copilotApi.askHistory(question).then((response) => response.data),
    onSuccess: (response) => {
      setHistoryAnswer(response.answer);
      setTranscript((current) => [
        ...current,
        {
          id: `history-${Date.now()}`,
          role: "assistant",
          content: response.answer,
          label: "History Insight",
        },
      ]);
    },
    onError: () => toast("error", "History analysis failed"),
  });

  const coverLetterMutation = useMutation({
    mutationFn: () =>
      copilotApi
        .generateCoverLetter(selectedJobId, coverLetterStyle, coverLetterTemplate || undefined)
        .then((response) => response.data),
    onSuccess: (response) => {
      setCoverLetter(response);
      setTranscript((current) => [
        ...current,
        {
          id: `letter-${Date.now()}`,
          role: "assistant",
          content: response.content,
          label: "Cover Letter Draft",
        },
      ]);
    },
    onError: () => toast("error", "Cover letter generation failed"),
  });

  const sendChat = (message: string) => {
    const trimmed = message.trim();
    if (!trimmed) return;

    setTranscript((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: trimmed,
        label: "You",
      },
    ]);
    chatMutation.mutate(trimmed);
  };

  const runHistoryQuestion = (question: string) => {
    const trimmed = question.trim();
    if (!trimmed) return;
    setHistoryQuestion(trimmed);
    askHistoryMutation.mutate(trimmed);
  };

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden p-0">
        <div className="border-b border-border bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent-primary)_10%,transparent),transparent_55%)] px-6 py-6">
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
            <div>
              <div className="text-xs font-medium tracking-[0.18em] text-text-muted uppercase">
                Prepare
              </div>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-text-primary">
                Copilot
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary">
                A focused workbench for strategy, historical recall, and job-specific writing. The
                layout follows a ChatGPT-style drafting lane with quieter operational context on the
                side.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge variant="info" size="md">
                  Context-aware chat
                </Badge>
                <Badge variant="default" size="md">
                  Ask your history
                </Badge>
                <Badge variant="success" size="md">
                  Cover letter drafts
                </Badge>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <MetricCard
                label="Recent Context"
                value={loadingJobs ? "..." : String(recentJobs?.items.length ?? 0)}
                hint="Fresh roles available to ground prompts."
                icon={<Briefcase size={18} weight="bold" />}
              />
            </div>
          </div>
        </div>

        <div className="px-6 py-4">
          <Tabs
            tabs={COPILOT_TABS.map((tab) => ({ ...tab }))}
            activeTab={activeTab}
            onChange={(nextTab) => startTransition(() => setActiveTab(nextTab as CopilotTab))}
          />
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,0.9fr)]">
        <Card className="min-h-[620px] p-0">
          <div className="flex h-full flex-col">
            <div className="border-b border-border px-6 py-4">
              <div className="flex flex-wrap items-end gap-4">
                <div className="min-w-[220px] flex-1">
                  <Select
                    label="Job context"
                    value={selectedJobId}
                    onChange={(event) => setSelectedJobId(event.target.value)}
                    options={jobOptions}
                    placeholder={loadingJobs ? "Loading jobs..." : "Choose a job"}
                  />
                </div>
                {selectedJob ? (
                  <div className="pb-1 text-sm text-text-secondary">
                    <span className="font-medium text-text-primary">{selectedJob.company_name ?? "Unknown company"}</span>
                    {" • "}
                    {selectedJob.location ?? "Flexible location"}
                  </div>
                ) : null}
              </div>
            </div>

            {activeTab === "assistant" ? (
              <>
                <div className="flex-1 space-y-4 overflow-auto px-6 py-5">
                  {transcript.length === 0 ? (
                    <EmptyState
                      icon={<Sparkle size={34} weight="bold" />}
                      title="Start with a strategic prompt"
                      description="Use the current job as context, or ask for a broader plan across your search."
                    />
                  ) : (
                    transcript.map((entry, index) => (
                      <motion.div
                        key={entry.id}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2, delay: index * 0.03 }}
                        className={cn(
                          "max-w-3xl rounded-[var(--radius-xl)] border px-4 py-4",
                          entry.role === "assistant"
                            ? "border-border bg-bg-secondary"
                            : "ml-auto border-accent-primary/25 bg-accent-primary/8"
                        )}
                      >
                        <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-text-muted">
                          {entry.label}
                        </div>
                        <div className="prose prose-sm max-w-none text-text-primary prose-p:leading-6 prose-headings:text-text-primary prose-strong:text-text-primary prose-li:text-text-secondary prose-p:text-text-secondary dark:prose-invert">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{entry.content}</ReactMarkdown>
                        </div>
                      </motion.div>
                    ))
                  )}
                  {chatMutation.isPending ? (
                    <div className="max-w-3xl rounded-[var(--radius-xl)] border border-border bg-bg-secondary px-4 py-4">
                      <Skeleton variant="text" className="h-4 w-28" />
                      <Skeleton variant="text" className="mt-3 h-4 w-full" />
                      <Skeleton variant="text" className="mt-2 h-4 w-5/6" />
                    </div>
                  ) : null}
                </div>

                <div className="border-t border-border px-6 py-5">
                  <div className="mb-3 flex flex-wrap gap-2">
                    {CHAT_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => sendChat(prompt)}
                        className="rounded-full border border-border bg-bg-tertiary px-3 py-1.5 text-xs text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                  <Textarea
                    value={chatInput}
                    onChange={(event) => setChatInput(event.target.value)}
                    placeholder="Ask for a search strategy, interview prep plan, or application triage."
                    className="min-h-[120px] bg-bg-secondary"
                  />
                  <div className="mt-3 flex justify-end">
                    <Button
                      variant="default"
                      onClick={() => sendChat(chatInput)}
                      disabled={!chatInput.trim() || chatMutation.isPending}
                    >
                      <Sparkle size={16} weight="bold" />
                      Send to Copilot
                    </Button>
                  </div>
                </div>
              </>
            ) : null}

            {activeTab === "history" ? (
              <div className="grid flex-1 gap-6 px-6 py-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                <div className="space-y-4">
                  <Card className="p-5">
                    <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                      <ClockCounterClockwise size={16} weight="bold" className="text-accent-primary" />
                      Ask your historical record
                    </div>
                    <p className="mt-2 text-sm leading-6 text-text-secondary">
                      Query applications, outcomes, and activity history for patterns that are hard to
                      spot in raw tables.
                    </p>
                    <Textarea
                      className="mt-4 min-h-[180px] bg-bg-secondary"
                      value={historyQuestion}
                      onChange={(event) => setHistoryQuestion(event.target.value)}
                      placeholder="Example: What changed in the roles that led to callbacks?"
                    />
                    <div className="mt-4 flex justify-end">
                      <Button
                        variant="default"
                        onClick={() => runHistoryQuestion(historyQuestion)}
                        disabled={!historyQuestion.trim() || askHistoryMutation.isPending}
                      >
                        <Brain size={16} weight="bold" />
                        Analyze history
                      </Button>
                    </div>
                  </Card>

                  <Card className="p-5">
                    <div className="text-sm font-semibold text-text-primary">Prompt starters</div>
                    <div className="mt-4 space-y-2">
                      {HISTORY_PROMPTS.map((prompt) => (
                        <button
                          key={prompt}
                          type="button"
                          onClick={() => runHistoryQuestion(prompt)}
                          className="w-full rounded-[var(--radius-lg)] border border-border bg-bg-secondary px-4 py-3 text-left text-sm text-text-secondary transition-colors hover:border-border-hover hover:text-text-primary"
                        >
                          {prompt}
                        </button>
                      ))}
                    </div>
                  </Card>
                </div>

                <Card className="p-5">
                  <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                    <Lightbulb size={16} weight="bold" className="text-accent-warning" />
                    What the system found
                  </div>
                  {askHistoryMutation.isPending ? (
                    <div className="mt-4 space-y-3">
                      <Skeleton variant="text" className="h-4 w-1/3" />
                      <Skeleton variant="text" className="h-4 w-full" />
                      <Skeleton variant="text" className="h-4 w-5/6" />
                      <Skeleton variant="text" className="h-4 w-4/5" />
                    </div>
                  ) : historyAnswer ? (
                    <div className="prose prose-sm mt-4 max-w-none text-text-primary prose-p:leading-6 prose-headings:text-text-primary prose-strong:text-text-primary prose-li:text-text-secondary prose-p:text-text-secondary dark:prose-invert">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{historyAnswer}</ReactMarkdown>
                    </div>
                  ) : (
                    <EmptyState
                      icon={<ArrowsOutCardinal size={32} weight="bold" />}
                      title="No history answer yet"
                      description="Run a question and the answer will land here as a reusable insight."
                    />
                  )}
                </Card>
              </div>
            ) : null}

            {activeTab === "letters" ? (
              <div className="grid flex-1 gap-6 px-6 py-5 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                <Card className="p-5">
                  <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                    <MagicWand size={16} weight="bold" className="text-accent-primary" />
                    Draft settings
                  </div>
                  <div className="mt-4 space-y-4">
                    <Select
                      label="Letter style"
                      value={coverLetterStyle}
                      onChange={(event) => setCoverLetterStyle(event.target.value)}
                      options={LETTER_STYLES}
                    />
                    <Textarea
                      label="Template guidance"
                      className="min-h-[240px] bg-bg-secondary"
                      value={coverLetterTemplate}
                      onChange={(event) => setCoverLetterTemplate(event.target.value)}
                      placeholder="Optional: specify voice, achievements to emphasize, or constraints to avoid."
                    />
                    <Button
                      variant="default"
                      onClick={() => coverLetterMutation.mutate()}
                      disabled={!selectedJobId || coverLetterMutation.isPending}
                    >
                      <FileText size={16} weight="bold" />
                      Generate draft
                    </Button>
                  </div>
                </Card>

                <Card className="p-5">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-text-primary">Draft preview</div>
                      <p className="mt-1 text-sm text-text-secondary">
                        Built against the selected role and ready to refine before export.
                      </p>
                    </div>
                    {coverLetter ? (
                      <Badge variant="success" size="md">
                        {coverLetter.style ?? "custom"}
                      </Badge>
                    ) : null}
                  </div>
                  {coverLetterMutation.isPending ? (
                    <div className="mt-4 space-y-3">
                      <Skeleton variant="text" className="h-4 w-1/4" />
                      <Skeleton variant="text" className="h-4 w-full" />
                      <Skeleton variant="text" className="h-4 w-full" />
                      <Skeleton variant="text" className="h-4 w-5/6" />
                    </div>
                  ) : coverLetter ? (
                    <div className="mt-4 whitespace-pre-wrap rounded-[var(--radius-xl)] border border-border bg-bg-secondary px-4 py-4 text-sm leading-6 text-text-secondary">
                      {coverLetter.content}
                    </div>
                  ) : (
                    <EmptyState
                      icon={<FileText size={32} weight="bold" />}
                      title="No cover letter yet"
                      description="Generate a job-specific draft and use the template field to push tone or structure."
                    />
                  )}
                </Card>
              </div>
            ) : null}
          </div>
        </Card>

        <div className="space-y-6">
          <Card className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
              <Briefcase size={16} weight="bold" className="text-accent-primary" />
              Active job context
            </div>
            {selectedJob ? (
              <div className="mt-4 space-y-3 text-sm">
                <div>
                  <div className="font-medium text-text-primary">{selectedJob.title}</div>
                  <div className="text-text-secondary">
                    {selectedJob.company_name ?? "Unknown company"} • {selectedJob.location ?? "Flexible"}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedJob.match_score !== null ? (
                    <Badge variant={selectedJob.match_score >= 0.7 ? "success" : "warning"}>
                      Match {Math.round(selectedJob.match_score * 100)}%
                    </Badge>
                  ) : null}
                  {selectedJob.remote_type ? <Badge variant="default">{selectedJob.remote_type}</Badge> : null}
                  {selectedJob.job_type ? <Badge variant="info">{selectedJob.job_type}</Badge> : null}
                </div>
                {selectedJob.summary_ai ? (
                  <p className="leading-6 text-text-secondary">{selectedJob.summary_ai}</p>
                ) : (
                  <p className="leading-6 text-text-muted">
                    No AI summary yet. The copilot will rely on title and company metadata.
                  </p>
                )}
              </div>
            ) : (
              <EmptyState
                icon={<Briefcase size={28} weight="bold" />}
                title="No job selected"
                description="Choose a role above to ground chat, history analysis, and drafting."
              />
            )}
          </Card>

          <Card className="p-5">
            <div className="text-sm font-semibold text-text-primary">How to use this surface</div>
            <div className="mt-4 space-y-3 text-sm leading-6 text-text-secondary">
              <p>Use Assistant for quick strategy and editing loops tied to a role.</p>
              <p>Use Ask History when you need recall over your own application patterns.</p>
              <p>Use Cover Letters when you want a structured output instead of conversational guidance.</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
