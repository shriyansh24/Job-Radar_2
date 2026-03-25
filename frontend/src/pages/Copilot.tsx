import {
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
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Select from "../components/ui/Select";
import Skeleton from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import Textarea from "../components/ui/Textarea";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import { Surface } from "../components/system/Surface";
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

function MarkdownBlock({ content }: { content: string }) {
  return (
    <div className="prose prose-sm max-w-none text-text-primary prose-p:leading-6 prose-headings:text-text-primary prose-strong:text-text-primary prose-li:text-text-secondary prose-p:text-text-secondary dark:prose-invert">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
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
      label: `${job.title} - ${job.company_name ?? "Unknown company"}`,
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

  const metrics = [
    {
      key: "context",
      label: "Recent Context",
      value: loadingJobs ? "..." : recentJobs?.items.length ?? 0,
      hint: "Fresh roles available to ground prompts.",
      icon: <Briefcase size={18} weight="bold" />,
    },
    {
      key: "transcript",
      label: "Transcript",
      value: transcript.length,
      hint: "Messages stored in the current drafting session.",
      icon: <Sparkle size={18} weight="bold" />,
      tone: "warning" as const,
    },
    {
      key: "mode",
      label: "Mode",
      value: COPILOT_TABS.find((tab) => tab.id === activeTab)?.label ?? "Assistant",
      hint: "Current copilot lane.",
      icon: <Brain size={18} weight="bold" />,
    },
    {
      key: "draft",
      label: "Letter",
      value: coverLetter?.style ?? "None",
      hint: "Latest cover-letter draft style.",
      icon: <FileText size={18} weight="bold" />,
      tone: "success" as const,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Prepare"
        title="Copilot"
        description="A role-aware drafting surface for job strategy, history analysis, and cover-letter generation."
        meta={
          <div className="flex flex-wrap gap-2">
            <Badge variant="info" size="sm">
              Context-aware chat
            </Badge>
            <Badge variant="warning" size="sm">
              Ask history
            </Badge>
            <Badge variant="success" size="sm">
              Cover letters
            </Badge>
          </div>
        }
      />

      <MetricStrip items={metrics} />

      <Surface tone="default" padding="md" radius="xl">
        <SectionHeader
          title="Copilot workspace"
          description="Switch between strategy chat, historical recall, and structured letter generation."
        />
        <Tabs
          className="mt-5"
          tabs={COPILOT_TABS.map((tab) => ({ ...tab }))}
          activeTab={activeTab}
          onChange={(nextTab) => startTransition(() => setActiveTab(nextTab as CopilotTab))}
        />
      </Surface>

      {activeTab === "assistant" ? (
        <SplitWorkspace
          primary={
            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader
                title="Assistant"
                description="Ground prompts against a role, then iterate through a lightweight transcript instead of a one-shot generation."
              />
              <div className="mt-6">
                <Select
                  label="Job context"
                  value={selectedJobId}
                  onChange={(event) => setSelectedJobId(event.target.value)}
                  options={jobOptions}
                  placeholder={loadingJobs ? "Loading jobs..." : "Choose a job"}
                />
              </div>

              <div className="mt-6 space-y-4">
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
                        "border-2 px-4 py-4 shadow-[var(--shadow-xs)]",
                        entry.role === "assistant"
                          ? "border-border bg-[var(--color-bg-tertiary)]"
                          : "ml-auto border-border bg-accent-primary/10"
                      )}
                    >
                      <div className="mb-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                        {entry.label}
                      </div>
                      <MarkdownBlock content={entry.content} />
                    </motion.div>
                  ))
                )}
                {chatMutation.isPending ? (
                  <div className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-4 shadow-[var(--shadow-xs)]">
                    <Skeleton variant="text" className="h-4 w-28" />
                    <Skeleton variant="text" className="mt-3 h-4 w-full" />
                    <Skeleton variant="text" className="mt-2 h-4 w-5/6" />
                  </div>
                ) : null}
              </div>

              <div className="mt-6 space-y-4 border-t-2 border-border pt-6">
                <div className="flex flex-wrap gap-2">
                  {CHAT_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => sendChat(prompt)}
                      className="border-2 border-border bg-[var(--color-bg-tertiary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-secondary transition-colors hover:bg-card hover:text-foreground"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
                <Textarea
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  placeholder="Ask for a search strategy, interview prep plan, or application triage."
                  className="min-h-[120px]"
                />
                <div className="flex justify-end">
                  <Button
                    variant="primary"
                    onClick={() => sendChat(chatInput)}
                    disabled={!chatInput.trim() || chatMutation.isPending}
                    icon={<Sparkle size={16} weight="bold" />}
                  >
                    Send to Copilot
                  </Button>
                </div>
              </div>
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="neutral"
                icon={<Briefcase size={18} weight="bold" />}
                title="Active job context"
                description={
                  selectedJob
                    ? `${selectedJob.title} at ${selectedJob.company_name ?? "Unknown company"}`
                    : "Choose a job above to ground the drafting context."
                }
              />
              {selectedJob ? (
                <Surface tone="default" padding="md" radius="xl">
                  <SectionHeader title="Job snapshot" />
                  <div className="mt-4 space-y-3 text-sm leading-6 text-text-secondary">
                    <p>{selectedJob.location ?? "Flexible location"}</p>
                    {selectedJob.match_score !== null ? (
                      <Badge variant={selectedJob.match_score >= 0.7 ? "success" : "warning"}>
                        Match {Math.round(selectedJob.match_score * 100)}%
                      </Badge>
                    ) : null}
                    <p>{selectedJob.summary_ai ?? "No AI summary yet. The assistant will rely on core job metadata."}</p>
                  </div>
                </Surface>
              ) : null}
            </div>
          }
        />
      ) : null}

      {activeTab === "history" ? (
        <SplitWorkspace
          primary={
            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader
                title="Ask your history"
                description="Query applications, outcomes, and activity history for patterns that are hard to spot in raw tables."
              />
              <Textarea
                className="mt-6 min-h-[180px]"
                value={historyQuestion}
                onChange={(event) => setHistoryQuestion(event.target.value)}
                placeholder="Example: What changed in the roles that led to callbacks?"
              />
              <div className="mt-4 flex justify-end">
                <Button
                  variant="primary"
                  onClick={() => runHistoryQuestion(historyQuestion)}
                  disabled={!historyQuestion.trim() || askHistoryMutation.isPending}
                  icon={<Brain size={16} weight="bold" />}
                >
                  Analyze history
                </Button>
              </div>

              <div className="mt-6 border-t-2 border-border pt-6">
                {askHistoryMutation.isPending ? (
                  <div className="space-y-3">
                    <Skeleton variant="text" className="h-4 w-1/3" />
                    <Skeleton variant="text" className="h-4 w-full" />
                    <Skeleton variant="text" className="h-4 w-5/6" />
                    <Skeleton variant="text" className="h-4 w-4/5" />
                  </div>
                ) : historyAnswer ? (
                  <MarkdownBlock content={historyAnswer} />
                ) : (
                  <EmptyState
                    icon={<Lightbulb size={32} weight="bold" />}
                    title="No history answer yet"
                    description="Run a question and the answer will land here as a reusable insight."
                  />
                )}
              </div>
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <Surface tone="default" padding="md" radius="xl">
                <SectionHeader title="Prompt starters" />
                <div className="mt-4 space-y-2">
                  {HISTORY_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => runHistoryQuestion(prompt)}
                      className="w-full border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-3 text-left text-sm leading-6 text-text-secondary transition-colors hover:bg-card hover:text-foreground"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </Surface>
              <StateBlock
                tone="warning"
                icon={<ClockCounterClockwise size={18} weight="bold" />}
                title="Use case"
                description="This lane is for pattern detection, not drafting tone. Ask when you need evidence from your own outcomes."
              />
            </div>
          }
        />
      ) : null}

      {activeTab === "letters" ? (
        <SplitWorkspace
          primary={
            <Surface tone="default" padding="lg" radius="xl">
              <SectionHeader
                title="Cover letter drafts"
                description="Generate a structured draft against the selected role, then refine it before exporting or saving."
              />
              <div className="mt-6 grid gap-4 lg:grid-cols-2">
                <Select
                  label="Job context"
                  value={selectedJobId}
                  onChange={(event) => setSelectedJobId(event.target.value)}
                  options={jobOptions}
                  placeholder={loadingJobs ? "Loading jobs..." : "Choose a job"}
                />
                <Select
                  label="Letter style"
                  value={coverLetterStyle}
                  onChange={(event) => setCoverLetterStyle(event.target.value)}
                  options={LETTER_STYLES}
                />
              </div>
              <Textarea
                label="Template guidance"
                className="mt-4 min-h-[220px]"
                value={coverLetterTemplate}
                onChange={(event) => setCoverLetterTemplate(event.target.value)}
                placeholder="Optional: specify voice, achievements to emphasize, or constraints to avoid."
              />
              <div className="mt-4 flex justify-end">
                <Button
                  variant="primary"
                  onClick={() => coverLetterMutation.mutate()}
                  disabled={!selectedJobId || coverLetterMutation.isPending}
                  icon={<MagicWand size={16} weight="bold" />}
                >
                  Generate draft
                </Button>
              </div>

              <div className="mt-6 border-t-2 border-border pt-6">
                {coverLetterMutation.isPending ? (
                  <div className="space-y-3">
                    <Skeleton variant="text" className="h-4 w-1/4" />
                    <Skeleton variant="text" className="h-4 w-full" />
                    <Skeleton variant="text" className="h-4 w-full" />
                    <Skeleton variant="text" className="h-4 w-5/6" />
                  </div>
                ) : coverLetter ? (
                  <div className="border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-4 text-sm leading-6 text-text-secondary shadow-[var(--shadow-xs)]">
                    {coverLetter.content}
                  </div>
                ) : (
                  <EmptyState
                    icon={<FileText size={32} weight="bold" />}
                    title="No cover letter yet"
                    description="Generate a job-specific draft and use the template field to push tone or structure."
                  />
                )}
              </div>
            </Surface>
          }
          secondary={
            <div className="space-y-4">
              <StateBlock
                tone="success"
                icon={<MagicWand size={18} weight="bold" />}
                title="Draft status"
                description={coverLetter ? `${coverLetter.style ?? "custom"} draft ready for review.` : "No draft has been generated yet."}
              />
              <StateBlock
                tone="neutral"
                icon={<Briefcase size={18} weight="bold" />}
                title="Selected job"
                description={
                  selectedJob
                    ? `${selectedJob.title} at ${selectedJob.company_name ?? "Unknown company"}`
                    : "Choose a job before generating a letter."
                }
              />
            </div>
          }
        />
      ) : null}
    </div>
  );
}
